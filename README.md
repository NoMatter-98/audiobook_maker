# audiobook_maker

## There are 3 parts of this tool so far, all written by python

Demo:
(1) 用于cosyvoice批量制作有声小说工具
https://lively-show-4b6.notion.site/20dd8f46699080338806c7f36e437ce2?pvs=74
(2)小说章节字数探测与自动分割器
分成章节后，依照token限制（一般模型输出窗口在8K），因此每章篇幅不宜超过4K。
https://lively-show-4b6.notion.site/20ed8f46699080a8b564f0f266163cb6?source=copy_link
(3)批量TXT转JSON脚本
可视化操作，忽略报错，有出json就表示成功运行

demo
默认使用的是gemini 2.0 flash lite

速度大概是1min一个txt文件

![Uploading image.png…]()

