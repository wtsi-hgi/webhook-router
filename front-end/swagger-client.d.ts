declare module "swagger-client"{
    export interface SwaggerClient<API>{
        apis: API
    }

    export interface SwaggerOptions{
        spec?: any,
        
        operationId?: any, // Either operationId, or you can use pathName + method
        pathName?: any,
        securities: object, // _named_ securities, will only be added to the request, if the spec indicates it. eg: {apiKey: 'abc'}
    }

    export function Swagger<API>(path: string, options?: SwaggerOptions): Promise<SwaggerClient<API>>;
}