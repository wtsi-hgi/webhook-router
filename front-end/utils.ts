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
    return {
        headers: {
            "Google-Auth-Token": googleToken
        }
    }
}