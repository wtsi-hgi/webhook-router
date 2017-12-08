declare interface SwaggerSpec{
    authorizations?: {
        [name: string]: any
    },
    requestInterceptor?: (request?: object) => any;
    responseInterceptor?: (resp: SwaggerResponse<any>) => any;
}

interface SwaggerOptions extends RequestInit {
    url: string;
    query?: string;
    requestInterceptor?: (req: Request) => Request;
    responseInterceptor?: (res: Response) => Response;
    userFetch?: (url: String, options: object) => Promise<any>;
}

interface SwaggerResolveOptions {
    url?: string;
    fetch: (url: String, options: object) => Promise<any>;
    mode: string;
    spec?: SwaggerSpec;
    http?: any;
    allowMetaPatches?: boolean;
    baseDoc?: any;
    modelPropertyMacro: Function
    parameterMacro: Function
    requestInterceptor: (request?: object) => any;
    responseInterceptor: (resp: SwaggerResponse<any>) => any;
}

interface SwaggerResolution {
    errors: any[];
    spec: any;
}

interface BasicAPI{
    [tag: string]: {
        [funcName: string]: (params?: object) => Promise<SwaggerResponse<any>>
    }
}

interface SwaggerResponse<Type> {
    ok: boolean;
    url: string;
    status: number;
    statusText: string;
    headers: {
        "content-type": string;
    };
    text: string;
    data: string;
    body: Type;
    obj: Type;
}

interface SwaggerAPI<APIType extends BasicAPI> {
    spec: SwaggerSpec;
    originalSpec: SwaggerSpec;
    errors: any;
    apis: APIType
}

declare var SwaggerCore: {
    http(options: SwaggerOptions): Promise<Response>;
    resolve(options: SwaggerResolveOptions): Promise<SwaggerResolution>;
    execute(params: object): any;
    buildRequest(params: object): any;
    clearCache(): any;
    <APIType extends BasicAPI = BasicAPI>(url: string, options?: SwaggerSpec): Promise<SwaggerAPI<APIType>>;
    <APIType extends BasicAPI = BasicAPI>(options: SwaggerSpec): Promise<SwaggerAPI<APIType>>;    
}

declare module "swagger-client" {
    export = SwaggerCore;
}