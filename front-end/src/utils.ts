import { Component } from "vue-router/types/router";

export function delay(time: number){
    return new Promise((resolve, reject) => {
        setTimeout(resolve, time);
    })
}

export function closeModal(vueTarget: any){
    return new Promise((resolve, reject) => {
        vueTarget.hide();
        vueTarget.$once("hidden", () => {
            resolve();
        })
    })
}

export async function promiseMap<InputType, OutputType>(array: InputType[], promise: (item: InputType) => Promise<OutputType>){
    let result = <OutputType[]>[];

    await Promise.all(array.map((item, index) => {
        return promise(item).then(returnItem => {
            result[index] = returnItem
        })
    }))

    return result;
}

/**
 * The default data for showing details of forms to users.
 * The keys of this data structure is also used for determining the data
 * that will be sent from the form to the server
 */
export var defaultFormData = {
    name: "",
    destination: "",
    no_ssl_verification: false
}

/**
 * Attributes which may be present on a form
 */
export var formAttributes = Object.keys(defaultFormData);

export function getRandomHex(bytes = 32){
    return Array.from(window.crypto.getRandomValues(new Uint8Array(bytes)))
        .map(x => x.toString(16)).join("")
}