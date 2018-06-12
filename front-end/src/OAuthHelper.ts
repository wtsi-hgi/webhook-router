/// <reference types="gapi.auth2" />
import * as ClientOAuth2 from "client-oauth2";
import * as utils from "./utils";
import {EventEmitter} from "events";
import {
    notEqual as assertNotEqual,
    equal as assertEqual
} from "assert";
import {
    camelCase,
    fromPairs,
    dropWhile
} from "lodash";

/**
 * Padding time for a reload of a token.
 * Half of this value will also be when the brower checks for the token being refreshed
 */
const RELOAD_PADDING = 10 * 60 * 1000; // 10 mins

type Maybe<T> = T | undefined;

function createCenterPopup(url, title, w, h) {
    // Fixes dual-screen position                         Most browsers      Firefox
    var dualScreenLeft = window.screenLeft != undefined ? window.screenLeft : window.screenX;
    var dualScreenTop = window.screenTop != undefined ? window.screenTop : window.screenY;

    var width = window.innerWidth ? window.innerWidth : document.documentElement.clientWidth ? document.documentElement.clientWidth : screen.width;
    var height = window.innerHeight ? window.innerHeight : document.documentElement.clientHeight ? document.documentElement.clientHeight : screen.height;

    var left = ((width / 2) - (w / 2)) + dualScreenLeft;
    var top = ((height / 2) - (h / 2)) + dualScreenTop;
    var newWindow = window.open(url, title, 'scrollbars=yes, width=' + w + ', height=' + h + ', top=' + top + ', left=' + left);

    if(!newWindow){
        throw Error("Login popups are being blocked. Please enable popups to continue.")
    }

    // Puts focus on the newWindow
    if (window.focus) {
        newWindow.focus();
    }

    return newWindow;
}

function notNully<A>(x: A){
    assertNotEqual(x, undefined);
    assertNotEqual(x, null);

    return x!;
}

function objectify(objectLike){
    return fromPairs<any>(Array.from(objectLike))
}

export default class OAuthHelper {
    private nonse = utils.getRandomHex(32);
    private clientOauth2Token: Maybe<ClientOAuth2.Token>;
    constructor(
        public name: string,
        private clientId: string,
        private authURI: string,
        private scopes: string[],
        public extraQueryParams = {}
    ){}
    readonly emitter = new EventEmitter();
    private readonly auth = new ClientOAuth2({
        clientId: this.clientId,
        authorizationUri: this.authURI,
        redirectUri: window.location.origin + "?oauth_callback",
        scopes: this.scopes,
        state: this.nonse,
        query: this.extraQueryParams
    });
    private refreshIntervalHandle: any;
    static readonly tokenChangeEvent = Symbol("tokenChange");
    private readonly localStorageName = this.name + "Token";

    get token() {
        if(this.clientOauth2Token == undefined)
            return undefined;

        return this.clientOauth2Token.accessToken;
    }

    get tokenExpireTime() {
        if(this.clientOauth2Token == undefined)
            return undefined;

        return (<any>this.clientOauth2Token).expires;
    }

    private changeToken(newToken: ClientOAuth2.Token){
        this.clientOauth2Token = newToken;

        this.emitter.emit(OAuthHelper.tokenChangeEvent, this.token);
    }

    private addRefreshTokenInterval(){
        this.refreshIntervalHandle = setInterval(() => {
            if(this.tokenExpireTime!.valueOf() - RELOAD_PADDING < Date.now()){
                this.refresh();
            }
        }, RELOAD_PADDING / 2);
    }

    async loadTryGetToken(): Promise<string | undefined> {
        const tokenStr = localStorage.getItem(this.localStorageName);

        if(tokenStr !== null){
            const token = JSON.parse(tokenStr);

            this.changeToken(
                this.auth.createToken(token)
            )

            await this.refresh();
            this.addRefreshTokenInterval();

            return this.token;
        }

        return undefined;
    }

    private getTokenFromURL(url: Location, nonse: string): ClientOAuth2.Token {
        const tmpURL = new URL(`http://localhost?${dropWhile(url.hash, x => x == "#" || x == "/").join("")}`);
        if(nonse !== tmpURL.searchParams.get("state")){
            throw Error(`Sanger OAuth error, incorrect nonse ${nonse} != ${tmpURL.searchParams.get("state")}`);
        }

        return this.auth.createToken(objectify(tmpURL.searchParams));
    }

    async promptLogin(): Promise<string | undefined>{
        console.log(`Navigating to ${this.auth.token.getUri()}`)
        const popupWindow = createCenterPopup(this.auth.token.getUri(), camelCase(this.name) + " Auth", 500, 500);

        const resolvedURL = <Location>(await new Promise((resolve, reject) => {
            const intervalHandle = setInterval(() => {
                let crossOriginBlocked = false;
                try{
                    popupWindow.location.href
                }
                catch{
                    crossOriginBlocked = true;
                }

                if(!crossOriginBlocked && popupWindow.location.href != undefined && popupWindow.location.href.search(location.origin) != -1){
                    resolve(popupWindow.location);

                    clearInterval(intervalHandle);
                }
                if(popupWindow.closed == true){
                    resolve(undefined);

                    clearInterval(intervalHandle);
                }
            }, 500);
        }));

        console.log("resolved to " + resolvedURL)

        if(!resolvedURL){
            console.log("returning undefined")
            return undefined;
        }


        const token = this.getTokenFromURL(resolvedURL, this.nonse);
        localStorage.setItem(this.localStorageName, JSON.stringify(token.data));
        this.changeToken(token);

        popupWindow.close();

        return this.token;
    }

    async logout() {
        localStorage.removeItem(this.localStorageName);
        clearInterval(this.refreshIntervalHandle);
    }

    private async refresh(): Promise<string> {
        if(notNully(this.clientOauth2Token).refreshToken !== undefined){
            const token = await this.clientOauth2Token!.refresh();

            this.changeToken(token);
        }

        return <string>this.token;
    }
}
