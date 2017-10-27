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

export function fetchErrorWrapper(errorFunction: (error: any) => any){
    return async (input: RequestInfo, init?: RequestInit) => {
        try{
            return await fetch(input, init);
        }
        catch(e){
            errorFunction(e);
            throw e;
        }
    }
}