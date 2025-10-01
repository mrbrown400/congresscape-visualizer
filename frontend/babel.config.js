module.exports = function (api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
    plugins: [
      [
        'module-resolver',
        {
          alias: {
            '@features': './src/features',
            '@navigation': './src/navigation',
            '@theme': './src/theme',
            '@components': './src/components',
            '@constants': './src/constants',
            '@hooks': './src/hooks',
            '@services': './src/services',
            '@utils': './src/utils'
          }
        }
      ],
      'react-native-reanimated/plugin'
    ]
  };
};
