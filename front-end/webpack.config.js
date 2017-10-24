module.exports = {
    entry: {
        index: './index.ts',
        "add-route": "./add-route/index.ts",
        "modify-route": "./modify-route/index.ts"
    },
    output: {
        filename: '[name].entry.js'
    },
    devtool: 'source-map',
    resolve: {
        extensions: ['.webpack.js', '.web.js', '.ts', '.tsx', '.js', '.json', '.html'],
        alias: {
            vue: 'vue/dist/vue.js'
        }
    },
    module: {
        loaders: [
            { test: /\.ts|\.tsx$/, loader: 'ts-loader' }
        ]
    }
}