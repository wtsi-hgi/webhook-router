export function getGoogleToken(){
    return new Promise<string | undefined>((reject, resolve) => {
        gapi.load('auth2', () => {
            gapi.auth2.init({
                client_id: '859663336690-q39h2o7j9o2d2vdeq1hm1815uqjfj5c9.apps.googleusercontent.com',
                fetch_basic_profile: false,
                scope: 'profile',
                hosted_domain: "sanger.ac.uk"
            }).then(auth => {
                if(auth.isSignedIn.get()){
                    resolve(auth.currentUser.get().getAuthResponse().id_token)
                }
                resolve(undefined)
        
                
            })
        });
    })
}

function renderFunc(){
    let signedIn;
    gapi.signin2.render("google-signin", {
        scope: "profile email",
        theme: 'dark',
        longtitle: true,
        onsuccess: (user) => {
            signedIn(user.getAuthResponse().id_token)
        }
    })
}