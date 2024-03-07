## VAL

欢迎使用VAL，这是一个资产侦察平台，旨在快速探索互联网资产并构建全面的资产信息库。致力于协助安全团队和渗透测试人员高效侦察和检索有关资产的信息，从攻击者的视角持续检测资产风险。

## 主要功能

1. 快速资产侦察：VAL支持对互联网资产的快速而全面的侦察，帮助构建基础资产信息数据库。 
2. 持续监控攻击面：从攻击者的角度出发，VAL持续检测和探测资产站点风险(包括且不限于,JS敏感信息探测,漏洞识别等)，帮助持续评估潜在的漏洞。

## 待完善功能

目前因为作者近期琐事缠身,目前仅仅完成了基础的功能,后续更新计划

1. 增加数据看板,统计资产信息

2. 增加站点敏感文件探测

3. 增加github监控功能

4. 如果其他师傅有希望增加的实用功能,可以联系作者(微信:lkwh125)

   

## 安装/部署

1. 通过源码部署

   ```
   git clone https://github.com/lamw-art/AST.git
   
   
   ```

## 界面介绍

1. 登录界面: 默认账号密码admin:admin123,!!!!!部署后请更改默认账号密码

   ![登录界面](https://128848-1309005458.cos.ap-beijing.myqcloud.com/typora/%E7%99%BB%E5%BD%95%E7%95%8C%E9%9D%A2.png)

2. 资产列表界面,新建资产会自动扫描资产目标获取子域名并对其进行站点探测任务得到站点

   ![资产列表](https://128848-1309005458.cos.ap-beijing.myqcloud.com/typora/%E8%B5%84%E4%BA%A7%E5%88%97%E8%A1%A8.png)

3. 站点管理界面

   ![站点管理](https://128848-1309005458.cos.ap-beijing.myqcloud.com/typora/%E7%AB%99%E7%82%B9%E7%AE%A1%E7%90%86.png)

4. 站点详情页面

   ![站点详情页面](https://128848-1309005458.cos.ap-beijing.myqcloud.com/typora/%E7%AB%99%E7%82%B9%E8%AF%A6%E6%83%85%E9%A1%B5%E9%9D%A2.png)

5. 指纹管理界面

   ![指纹管理](https://128848-1309005458.cos.ap-beijing.myqcloud.com/typora/%E6%8C%87%E7%BA%B9%E7%AE%A1%E7%90%86.png)

   

6. 本地POC信息(每次执行漏洞扫描时会同步该信息)

   ![本地POC信息](https://128848-1309005458.cos.ap-beijing.myqcloud.com/typora/%E6%9C%AC%E5%9C%B0POC%E4%BF%A1%E6%81%AF.png)
