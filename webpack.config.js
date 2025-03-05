const path = require('path');

module.exports = {
  mode: 'development',
  entry: './components/index.js',
  output: {
    filename: 'listing-wizard.js',
    path: path.resolve(__dirname, 'static/js'),
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env', '@babel/preset-react']
          }
        }
      }
    ]
  },
  resolve: {
    extensions: ['.js', '.jsx']
  }
};