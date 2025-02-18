# DeepOne-Mod
修改源码实现剧情汉化，汉化由[三金](https://github.com/lisanjin)提供

- 已经修改包名，可以和原版共存
- APP支持热更新，无需每次手动更新

## 功能/原理
- 修改project.js重定向剧本文件的请求
- 修改manifest将热更新地址定向到自定义的服务器，由服务器提供修补后的热更新源码，确保热更新后汉化功能不会失效
- 取消剧本文件的缓存，确保汉化能够即时更新
- 替换游戏剧情字体，由原版字体humming与方正轻吟体合并所得
- 对于没有汉化的剧本，服务器会重定向回原剧本

## 下载地址
本仓库[Releases](https://github.com/anosu/DeepOne-Mod/releases)

## 其他
project.js的更新脚本见仓库
