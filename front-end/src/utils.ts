export function delay(time: number){
    return new Promise((resolve, reject) => {
        setTimeout(resolve, time);
    })
}

export function closeModal(modal: HTMLElement){
    return new Promise((resolve, reject) => {
        $(modal).modal("hide")
        $(modal).one("hidden.bs.modal", () => {
            resolve();
        })
    })
}

export function getAuthOptions(googleToken: string){
    let testUserProp = localStorage.getItem("testUser");
    if(testUserProp != undefined){
        return {
            headers: {
                user: testUserProp
            }
        }
    }

    return {
        headers: {
            "Google-Auth-Token": googleToken
        }
    }
}

/**
 * The default data for showing details of forms to users
 */
export var defaultFormData = {
    name: "",
    destination: "",
    no_ssl_verification: false
}