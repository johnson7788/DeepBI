# Version
### 2.0.3 
- The problem of generating pictures in the process of modifying report dialog .
- The problem of not finding function in modifying auxiliary data analysis dialog. 
- Added the csv automatic data analysis function. 
- Modify the exe startup problem



### 2.0.2
- Adapt an existing function call to the new openai version of tools

### 2.0.1
- Add support LLM configurations,including BaiduQianfan、AliBailian

### 2.0.0
- Supports different LLM configurations, including Azure openai, AwsClaude3 sonnetDeepSeek, DeepSeek and other LLMS

### 1.3.0
- Update DeepBI logo
- Update ubuntu install shell,make log dir and write pid file
- Update python version and fix chmod bug
- Fix TaskSelectorAgent BUG.
  Fixed a BUG in the task workflow where Agent response was not standardized and the conversation could not continue
- The front-end web page adds refresh storage response
- Fix Echart BUG.
Fix Echart code is not standardized, resulting in page crash BUG
- New Echart code specification detection and retry mechanism to optimize the success rate of Echart chart generation
- Optimizes Echart workflow to support Echart chart generation with large data volumes
- Optimize Echart workflow context to reduce token consumption


### 1.2.3
- fix some bug,such as Echarts 、json suport、 html output、sql query
- support Azure API key
- Added region scaling and scroll legend features
- Added the ubuntu start and stop script



### 1.2.2
- Add mongodb database support.
- Fix the report generation path bug.


### 1.2.1
BUG fixes:
- Fixed the problem of token statistics in some network environments.
- Fixed the problem of Chinese characters in the report generated by autopilot in English version.
- Fixed the problem of chart Agent's unformatted output in the report module causing chart generation failure in a small number of cases.

New function:
- Add one-click copy function to optimize Agent session records in copy show work.

Optimize:
- Optimize some Agent prompt and data source comment to reduce token consumption in dialogues.
- Optimize user feedback, involving error feedback /apikey error/insufficient apikey balance and other information.

### 1.2.0
- Added the AI intelligent Prettify Large-screen function
- Fiex some bugs
- Updated the installation and usage instructions

### 1.1.0
- Externalize Docker code.
- Organize the Python environment and delete the original environment files.
- Rename the project.
- Fixing some installation instruction Markdown files and the installation shell script.

### 1.0.0
- first release
