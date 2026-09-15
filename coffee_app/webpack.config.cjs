const path = require('path')
const fs = require('fs')
const webpack = require('webpack')
const HtmlWebpackPlugin = require('html-webpack-plugin')
const CopyWebpackPlugin = require('copy-webpack-plugin')
const dotenv = require('dotenv')

const envKeys = [
  'APP_MODE',
  'CHAT_ENABLED',
  'ESPRESSO_MACHINE_LABEL',
  'GRINDER_LABEL',
  'DEFAULT_DOSE_G',
  'DEFAULT_GRIND',
  'DEFAULT_BASKET',
  'DEFAULT_PAPER',
  'DEFAULT_TEMP',
  'DEFAULT_PUCK_SCREEN',
  'PRIVY_APP_ID',
  'PRIVY_CLIENT_ID',
  'API_BASE_URL',
  'DISABLE_DEV_WORKOUT',
  'DEV_PREVIEW_WORKOUT',
  'APP_VERSION',
  'BUILD_TIME',
  'VERCEL_ENV',
  'VERCEL_GIT_COMMIT_SHA',
  'VERCEL_GIT_COMMIT_TIMESTAMP',
  'VERCEL_GIT_COMMIT_REF',
]

const parseEnvFile = (filename) => {
  const envPath = path.resolve(__dirname, filename)
  if (!fs.existsSync(envPath)) return {}
  return dotenv.parse(fs.readFileSync(envPath))
}

const loadEnv = () => {
  const parsed = {
    ...parseEnvFile('../.env'),
    ...parseEnvFile('.env'),
    ...parseEnvFile('.env.local'),
    ...process.env,
  }
  return envKeys.reduce((acc, key) => {
    const value = parsed[key] ?? ''
    acc[key] = value
    return acc
  }, {})
}

module.exports = (_env, argv) => {
  const mode = argv.mode || 'development'
  const env = { ...loadEnv(), NODE_ENV: mode }
  if (!env.BUILD_TIME) {
    env.BUILD_TIME = new Date().toISOString()
  }
  const serviceWorkerBuildId = [
    env.VERCEL_GIT_COMMIT_SHA || env.APP_VERSION || 'build',
    env.BUILD_TIME,
  ].join('-').replace(/[^a-zA-Z0-9_-]/g, '').slice(0, 64)

  return {
    mode,
    entry: path.resolve(__dirname, 'src', env.APP_MODE === 'selfhost' ? 'bootstrap.selfhost.tsx' : 'bootstrap.tsx'),
    output: {
      path: path.resolve(__dirname, 'dist'),
      filename: mode === 'production' ? 'assets/[name].[contenthash].js' : 'assets/[name].js',
      publicPath: '/',
      clean: true,
    },
    devtool: mode === 'production' ? 'source-map' : 'eval-cheap-module-source-map',
    resolve: {
      extensions: ['.tsx', '.ts', '.js'],
      alias: {
        '@farcaster/mini-app-solana': false,
      },
    },
    target: ['web', 'es2020'],
    module: {
      rules: [
        {
          test: /\.tsx?$/,
          use: {
            loader: 'ts-loader',
            options: {
              transpileOnly: true,
            },
          },
          exclude: /node_modules/,
        },
        {
          test: /\.css$/,
          use: ['style-loader', 'css-loader'],
        },
        {
          test: /\.(png|jpg|jpeg|gif|svg|mp3)$/i,
          type: 'asset/resource',
          generator: {
            filename: 'assets/[name][ext]',
          },
        },
      ],
    },
    plugins: [
      new HtmlWebpackPlugin({
        template: path.resolve(__dirname, 'public', 'index.html'),
      }),
      new CopyWebpackPlugin({
        patterns: [
          {
            from: path.resolve(__dirname, 'public', 'sw.js'),
            to: path.resolve(__dirname, 'dist', 'sw.js'),
            transform: (content) => Buffer.from(
              content.toString().replace('__COFFEE_BUILD_ID__', serviceWorkerBuildId)
            ),
          },
          {
            from: path.resolve(__dirname, 'public'),
            noErrorOnMissing: true,
            to: path.resolve(__dirname, 'dist'),
            globOptions: {
              ignore: ['**/index.html', '**/sw.js'],
            },
          },
        ],
      }),
      new webpack.DefinePlugin({
        'process.env': JSON.stringify(env),
      }),
    ],
    devServer: {
      static: {
        directory: path.resolve(__dirname, 'public'),
      },
      allowedHosts: 'all',
      historyApiFallback: true,
      port: 5176,
      host: '::',
      hot: true,
    },
  }
}
