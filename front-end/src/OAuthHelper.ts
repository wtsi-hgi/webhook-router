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
        if(this.tokenExpireTime!.valueOf() - RELOAD_PADDING < Date.now()){
            this.refresh();
        }

        this.refreshIntervalHandle = setInterval(() => {
            if(this.tokenExpireTime!.valueOf() - RELOAD_PADDING < Date.now()){
                this.refresh();
            }
        }, RELOAD_PADDING / 2);
    }

    async loadTryGetToken(): Promise<string | undefined> {
        const tokenJSONStr = localStorage.getItem(this.localStorageName);

        if(tokenJSONStr !== null){
            let token = JSON.parse(tokenJSONStr);
            token.expires_in = new Date(token.expires_in);

            this.changeToken(
                this.auth.createToken(token)
            )

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

    resolveUrlFromWindow(newWindow: Window): Promise<Location>{
        return new Promise((resolve, _) => {
            const intervalHandle = setInterval(() => {
                let crossOriginBlocked = false;
                try{
                    newWindow.location.href
                }
                catch{
                    crossOriginBlocked = true;
                }

                if(!crossOriginBlocked && newWindow.location.href != undefined && newWindow.location.href.search(location.origin) != -1){
                    resolve(newWindow.location);

                    clearInterval(intervalHandle);
                }
                if(newWindow.closed == true){
                    resolve(undefined);

                    clearInterval(intervalHandle);
                }
            }, 500);
        })
    }

    async setTokenFromWindow(newWindow: Window){
        const resolvedURL = await this.resolveUrlFromWindow(newWindow);

        if(!resolvedURL){
            return undefined;
        }

        const token = this.getTokenFromURL(resolvedURL, this.nonse);
        token.data.expires_in = (<any>token).expires;

        localStorage.setItem(this.localStorageName, JSON.stringify(token.data));
        this.changeToken(token);
    }

    promptLogin(): Promise<string | undefined>{
        console.log(this.auth.token.getUri());
        // NOTE: this needs to be not in a Promise function - it needs to be directly called from a user action
        const popupWindow = createCenterPopup(this.auth.token.getUri(), camelCase(this.name) + " Auth", 500, 500);

        return (async () => {
            await this.setTokenFromWindow(popupWindow);

            popupWindow.close();

            return this.token;
        })()
    }

    async logout() {
        localStorage.removeItem(this.localStorageName);
        clearInterval(this.refreshIntervalHandle);
    }

    private async refresh(): Promise<string> {
        let frame = document.createElement("iframe");
        frame.src = this.auth.token.getUri();
        frame.style.display = "none";
        document.body.appendChild(frame);

        await this.setTokenFromWindow(notNully(frame.contentWindow));

        document.body.removeChild(frame);

        return <string>this.token;
    }
}
