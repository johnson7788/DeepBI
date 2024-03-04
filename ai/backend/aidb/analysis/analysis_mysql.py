import traceback
import json
from ai.backend.util.write_log import logger
from ai.backend.base_config import CONFIG
from ai.backend.util import database_util
from .analysis import Analysis
import re
import ast
from ai.agents.agentchat import AssistantAgent
from ai.backend.util import base_util

max_retry_times = CONFIG.max_retry_times


class AnalysisMysql(Analysis):

    async def deal_question(self, json_str, message):
        """
        Process mysql data source and select the corresponding workflow
        """
        result = {'state': 200, 'data': {}, 'receiver': ''}
        q_sender = json_str['sender']
        q_data_type = json_str['data']['data_type']
        print('q_data_type : ', q_data_type)
        q_str = json_str['data']['content']

        print("self.agent_instance_util.api_key_use :", self.agent_instance_util.api_key_use)
        if not self.agent_instance_util.api_key_use:
            re_check = await self.check_api_key()
            print('re_check : ', re_check)
            if not re_check:
                return

        if q_sender == 'user':
            if q_data_type == 'question':
                # print("agent_instance_util.base_message :", self.agent_instance_util.base_message)
                if self.agent_instance_util.base_message is not None:
                    await self.start_chatgroup(q_str)

                else:
                    await self.put_message(500, receiver=CONFIG.talker_user, data_type=CONFIG.type_answer,
                                           content=self.error_miss_data)
        elif q_sender == 'bi':
            if q_data_type == CONFIG.type_comment:
                await self.check_data_base(q_str)
            elif q_data_type == CONFIG.type_comment_first:
                if json_str.get('data').get('language_mode'):
                    q_language_mode = json_str['data']['language_mode']
                    if q_language_mode == CONFIG.language_chinese or q_language_mode == CONFIG.language_english or q_language_mode == CONFIG.language_japanese:
                        self.set_language_mode(q_language_mode)
                        self.agent_instance_util.set_language_mode(q_language_mode)

                if CONFIG.database_model == 'online':
                    databases_id = json_str['data']['databases_id']
                    db_id = str(databases_id)
                    obj = database_util.Main(db_id)
                    if_suss, db_info = obj.run()
                    if if_suss:
                        self.agent_instance_util.base_mysql_info = ' When connecting to the database, be sure to bring the port. This is mysql database info :' + '\n' + str(
                            db_info)
                        self.agent_instance_util.set_base_message(q_str)
                        self.agent_instance_util.db_id = db_id


                else:
                    self.agent_instance_util.set_base_message(q_str)

                await self.get_data_desc(q_str)
            elif q_data_type == CONFIG.type_comment_second:
                if json_str.get('data').get('language_mode'):
                    q_language_mode = json_str['data']['language_mode']
                    if q_language_mode == CONFIG.language_chinese or q_language_mode == CONFIG.language_english or q_language_mode == CONFIG.language_japanese:
                        self.set_language_mode(q_language_mode)
                        self.agent_instance_util.set_language_mode(q_language_mode)

                if CONFIG.database_model == 'online':
                    databases_id = json_str['data']['databases_id']
                    db_id = str(databases_id)
                    print("db_id:", db_id)
                    obj = database_util.Main(db_id)
                    if_suss, db_info = obj.run()
                    if if_suss:
                        self.agent_instance_util.base_mysql_info = '  When connecting to the database, be sure to bring the port. This is mysql database info :' + '\n' + str(
                            db_info)
                        self.agent_instance_util.set_base_message(q_str)
                        self.agent_instance_util.db_id = db_id
                else:
                    self.agent_instance_util.set_base_message(q_str)

                await self.put_message(200, receiver=CONFIG.talker_bi, data_type=CONFIG.type_comment_second,
                                       content='')
            elif q_data_type == 'mysql_code' or q_data_type == 'chart_code' or q_data_type == 'delete_chart' or q_data_type == 'ask_data':
                self.delay_messages['bi'][q_data_type].append(message)
                print("delay_messages : ", self.delay_messages)
                return
        else:
            print('error : q_sender is not user or bi')
            await self.put_message(500, receiver=CONFIG.talker_bi, data_type=CONFIG.type_comment_second,
                                   content='error : q_sender is not user or bi')

    async def task_base(self, qustion_message):
        """ Task type: mysql data analysis"""
        try:
            error_times = 0
            for i in range(max_retry_times):
                try:
                    base_mysql_assistant = self.get_agent_base_mysql_assistant()
                    python_executor = self.agent_instance_util.get_agent_python_executor()

                    await python_executor.initiate_chat(
                        base_mysql_assistant,
                        message=self.agent_instance_util.base_message + '\n' + self.question_ask + '\n' + str(
                            qustion_message),
                    )

                    answer_message = python_executor.chat_messages[base_mysql_assistant]
                    print("answer_message: ", answer_message)

                    for i in range(len(answer_message)):
                        answer_mess = answer_message[len(answer_message) - 1 - i]
                        # print("answer_mess :", answer_mess)
                        if answer_mess['content'] and answer_mess['content'] != 'TERMINATE':
                            print("answer_mess['content'] ", answer_mess['content'])
                            return answer_mess['content']

                except Exception as e:
                    traceback.print_exc()
                    logger.error("from user:[{}".format(self.user_name) + "] , " + "error: " + str(e))
                    error_times = error_times + 1

            if error_times >= max_retry_times:
                return self.error_message_timeout

        except Exception as e:
            traceback.print_exc()
            logger.error("from user:[{}".format(self.user_name) + "] , " + "error: " + str(e))

        return self.agent_instance_util.data_analysis_error

    def get_agent_base_mysql_assistant(self):
        """ Basic Agent, processing mysql data source """
        base_mysql_assistant = AssistantAgent(
            name="base_mysql_assistant",
            system_message="""You are a helpful AI assistant.
                  Solve tasks using your coding and language skills.
                  In the following cases, suggest python code (in a python coding block) for the user to execute.
                      1. When you need to collect info, use the code to output the info you need, for example, browse or search the web, download/read a file, print the content of a webpage or a file, get the current date/time, check the operating system. After sufficient info is printed and the task is ready to be solved based on your language skill, you can solve the task by yourself.
                      2. When you need to perform some task with code, use the code to perform the task and output the result. Finish the task smartly.
                  Solve the task step by step if you need to. If a plan is not provided, explain your plan first. Be clear which step uses code, and which step uses your language skill.
                  When using code, you must indicate the script type in the code block. The user cannot provide any other feedback or perform any other action beyond executing the code you suggest. The user can't modify your code. So do not suggest incomplete code which requires users to modify. Don't use a code block if it's not intended to be executed by the user.
                  If you want the user to save the code in a file before executing it, put # filename: <filename> inside the code block as the first line. Don't include multiple code blocks in one response. Do not ask users to copy and paste the result. Instead, use 'print' function for the output when relevant. Check the execution result returned by the user.
                  If the result indicates there is an error, fix the error and output the code again. Suggest the full code instead of partial code or code changes. If the error can't be fixed or if the task is not solved even after the code is executed successfully, analyze the problem, revisit your assumption, collect additional info you need, and think of a different approach to try.
                  When you find an answer, verify the answer carefully. Include verifiable evidence in your response if possible.
                  In any case (even if I ask you to output an html file), please output the results directly and do not save them to a file.
                  Reply "TERMINATE" in the end when everything is done.
                  When you find an answer,  You are a report analysis, you have the knowledge and skills to turn raw data into information and insight, which can be used to make business decisions.include your analysis in your reply.
                  Be careful to avoid using mysql special keywords in mysql code.
                  """ + '\n' + self.agent_instance_util.base_mysql_info + '\n' + CONFIG.python_base_dependency + '\n' + self.agent_instance_util.quesion_answer_language,
            human_input_mode="NEVER",
            user_name=self.user_name,
            websocket=self.websocket,
            llm_config={
                "config_list": self.agent_instance_util.config_list_gpt4_turbo,
                "request_timeout": CONFIG.request_timeout,
            },
            openai_proxy=self.agent_instance_util.openai_proxy,
        )
        return base_mysql_assistant

    async def task_generate_echart(self, qustion_message):
        """ test echart code"""
        return await self.test_echrts_code()
        try:
            base_content = []
            base_mess = []
            report_demand_list = []
            json_str = ""
            error_times = 0
            use_cache = True
            for i in range(max_retry_times):
                try:
                    mysql_echart_assistant = self.agent_instance_util.get_agent_mysql_echart_assistant(
                        use_cache=use_cache)
                    python_executor = self.agent_instance_util.get_agent_python_executor()

                    await python_executor.initiate_chat(
                        mysql_echart_assistant,
                        message=self.agent_instance_util.base_message + '\n' + self.question_ask + '\n' + str(
                            qustion_message),
                    )

                    answer_message = mysql_echart_assistant.chat_messages[python_executor]

                    for answer_mess in answer_message:
                        # print("answer_mess :", answer_mess)
                        if answer_mess['content']:
                            if str(answer_mess['content']).__contains__('execution succeeded'):

                                answer_mess_content = str(answer_mess['content']).replace('\n', '')

                                print("answer_mess: ", answer_mess)
                                match = re.search(
                                    r"\[.*\]", answer_mess_content.strip(), re.MULTILINE | re.IGNORECASE | re.DOTALL
                                )

                                if match:
                                    json_str = match.group()
                                print("json_str : ", json_str)
                                # report_demand_list = json.loads(json_str)

                                chart_code_str = str(json_str).replace("\n", "")
                                if len(chart_code_str) > 0:
                                    print("chart_code_str: ", chart_code_str)
                                    if base_util.is_json(chart_code_str):
                                        report_demand_list = json.loads(chart_code_str)

                                        print("report_demand_list: ", report_demand_list)

                                        for jstr in report_demand_list:
                                            if str(jstr).__contains__('echart_name') and str(jstr).__contains__(
                                                'echart_code'):
                                                base_content.append(jstr)
                                    else:
                                        # String instantiated as object
                                        report_demand_list = ast.literal_eval(chart_code_str)
                                        print("report_demand_list: ", report_demand_list)
                                        for jstr in report_demand_list:
                                            if str(jstr).__contains__('echart_name') and str(jstr).__contains__(
                                                'echart_code'):
                                                base_content.append(jstr)

                    print("base_content: ", base_content)
                    base_mess = []
                    base_mess.append(answer_message)
                    break


                except Exception as e:
                    traceback.print_exc()
                    logger.error("from user:[{}".format(self.user_name) + "] , " + "error: " + str(e))
                    error_times = error_times + 1
                    use_cache = False

            if error_times >= max_retry_times:
                return self.error_message_timeout

            logger.info(
                "from user:[{}".format(self.user_name) + "] , " + "，report_demand_list" + str(report_demand_list))

            bi_proxy = self.agent_instance_util.get_agent_bi_proxy()
            is_chart = False
            # Call the interface to generate pictures
            for img_str in base_content:
                echart_name = img_str.get('echart_name')
                echart_code = img_str.get('echart_code')

                if len(echart_code) > 0 and str(echart_code).__contains__('x'):
                    is_chart = True
                    print("echart_name : ", echart_name)
                    # 格式化echart_code
                    # if base_util.is_json(str(echart_code)):
                    #     json_obj = json.loads(str(echart_code))
                    #     echart_code = json.dumps(json_obj)

                    re_str = await bi_proxy.run_echart_code(str(echart_code), echart_name)
                    base_mess.append(re_str)

            error_times = 0
            for i in range(max_retry_times):
                try:
                    planner_user = self.agent_instance_util.get_agent_planner_user()
                    analyst = self.agent_instance_util.get_agent_analyst()

                    question_supplement = 'Please make an analysis and summary in English, including which charts were generated, and briefly introduce the contents of these charts.'
                    if self.language_mode == CONFIG.language_chinese:

                        if is_chart:
                            question_supplement = " 请用中文，简单介绍一下已生成图表中的数据内容."
                        else:
                            question_supplement = " 请用中文，从上诉对话中分析总结出问题的答案."
                    elif self.language_mode == CONFIG.language_japanese:
                        if is_chart:
                            question_supplement = " 生成されたグラフのデータ内容について、簡単に日本語で説明してください。"
                        else:
                            question_supplement = " 上記の対話から問題の答えを分析し、日本語で要約してください。"

                    await planner_user.initiate_chat(
                        analyst,
                        message=str(
                            base_mess) + '\n' + self.question_ask + '\n' + question_supplement,
                    )

                    answer_message = planner_user.last_message()["content"]
                    return answer_message

                except Exception as e:
                    traceback.print_exc()
                    logger.error("from user:[{}".format(self.user_name) + "] , " + "error: " + str(e))
                    error_times = error_times + 1

            if error_times == max_retry_times:
                return self.error_message_timeout

        except Exception as e:
            traceback.print_exc()
            logger.error("from user:[{}".format(self.user_name) + "] , " + "error: " + str(e))
        return self.agent_instance_util.data_analysis_error
    
    async def test_echrts_code(self):
        base_content = []
        base_mess = []
        report_demand_list = []
        json_str = ""
        error_times = 0
        use_cache = True
        match = [{"echart_name": "\u9500\u552e\u989d\u524d15\u7684\u57ce\u5e02", "echart_code": "{\n \"animation\": true,\n \"animationThreshold\": 2000,\n \"animationDuration\": 1000,\n \"animationEasing\": \"cubicOut\",\n \"animationDelay\": 0,\n \"animationDurationUpdate\": 300,\n \"animationEasingUpdate\": \"cubicOut\",\n \"animationDelayUpdate\": 0,\n \"aria\": {\n \"enabled\": false\n },\n \"color\": [\n \"#5470c6\",\n \"#91cc75\",\n \"#fac858\",\n \"#ee6666\",\n \"#73c0de\",\n \"#3ba272\",\n \"#fc8452\",\n \"#9a60b4\",\n \"#ea7ccc\"\n ],\n \"series\": [\n {\n \"type\": \"bar\",\n \"name\": \"\\u9500\\u552e\\u989d\",\n \"legendHoverLink\": true,\n \"data\": [\n 77152.37,\n 60435.08,\n 54605.79,\n 52122.4,\n 51536.25,\n 48514.54,\n 44239.48,\n 43685.18,\n 43378.88,\n 41725.99,\n 41578.25,\n 39900.42,\n 39441.41,\n 36363.93,\n 35670.39\n ],\n \"realtimeSort\": false,\n \"showBackground\": false,\n \"stackStrategy\": \"samesign\",\n \"cursor\": \"pointer\",\n \"barMinHeight\": 0,\n \"barCategoryGap\": \"20%\",\n \"barGap\": \"30%\",\n \"large\": false,\n \"largeThreshold\": 400,\n \"seriesLayoutBy\": \"column\",\n \"datasetIndex\": 0,\n \"clip\": true,\n \"zlevel\": 0,\n \"z\": 2,\n \"label\": {\n \"show\": true,\n \"margin\": 8\n }\n }\n ],\n \"legend\": [\n {\n \"data\": [\n \"\\u9500\\u552e\\u989d\"\n ],\n \"selected\": {},\n \"show\": true,\n \"padding\": 5,\n \"itemGap\": 10,\n \"itemWidth\": 25,\n \"itemHeight\": 14,\n \"backgroundColor\": \"transparent\",\n \"borderColor\": \"#ccc\",\n \"borderWidth\": 1,\n \"borderRadius\": 0,\n \"pageButtonItemGap\": 5,\n \"pageButtonPosition\": \"end\",\n \"pageFormatter\": \"{current}/{total}\",\n \"pageIconColor\": \"#2f4554\",\n \"pageIconInactiveColor\": \"#aaa\",\n \"pageIconSize\": 15,\n \"animationDurationUpdate\": 800,\n \"selector\": false,\n \"selectorPosition\": \"auto\",\n \"selectorItemGap\": 7,\n \"selectorButtonGap\": 10\n }\n ],\n \"tooltip\": {\n \"show\": true,\n \"trigger\": \"item\",\n \"triggerOn\": \"mousemove|click\",\n \"axisPointer\": {\n \"type\": \"line\"\n },\n \"showContent\": true,\n \"alwaysShowContent\": false,\n \"showDelay\": 0,\n \"hideDelay\": 100,\n \"enterable\": false,\n \"confine\": false,\n \"appendToBody\": false,\n \"transitionDuration\": 0.4,\n \"textStyle\": {\n \"fontSize\": 14\n },\n \"borderWidth\": 0,\n \"padding\": 5,\n \"order\": \"seriesAsc\"\n },\n \"xAxis\": [\n {\n \"type\": \"category\",\n \"name\": \"\\u57ce\\u5e02\",\n \"show\": true,\n \"scale\": false,\n \"nameLocation\": \"end\",\n \"nameGap\": 15,\n \"gridIndex\": 0,\n \"inverse\": false,\n \"offset\": 0,\n \"splitNumber\": 5,\n \"minInterval\": 0,\n \"splitLine\": {\n \"show\": true,\n \"lineStyle\": {\n \"show\": true,\n \"width\": 1,\n \"opacity\": 1,\n \"curveness\": 0,\n \"type\": \"solid\"\n }\n },\n \"data\": [\n \"Manila\",\n \"Brisbane\",\n \"Sydney\",\n \"London\",\n \"Bangkok\",\n \"Mexico City\",\n \"Santo Domingo\",\n \"Managua\",\n \"Melbourne\",\n \"Gold Coast\",\n \"Jakarta\",\n \"Berlin\",\n \"Perth\",\n \"San Salvador\",\n \"Vienna\"\n ]\n }\n ],\n \"yAxis\": [\n {\n \"type\": \"value\",\n \"name\": \"\\u9500\\u552e\\u989d\",\n \"show\": true,\n \"scale\": false,\n \"nameLocation\": \"end\",\n \"nameGap\": 15,\n \"gridIndex\": 0,\n \"inverse\": false,\n \"offset\": 0,\n \"splitNumber\": 5,\n \"minInterval\": 0,\n \"splitLine\": {\n \"show\": true,\n \"lineStyle\": {\n \"show\": true,\n \"width\": 1,\n \"opacity\": 1,\n \"curveness\": 0,\n \"type\": \"solid\"\n }\n }\n }\n ],\n \"title\": [\n {\n \"show\": true,\n \"text\": \"\\u9500\\u552e\\u989d\\u524d15\\u7684\\u57ce\\u5e02\",\n \"target\": \"blank\",\n \"subtarget\": \"blank\",\n \"padding\": 5,\n \"itemGap\": 10,\n \"textAlign\": \"auto\",\n \"textVerticalAlign\": \"auto\",\n \"triggerEvent\": false\n }\n ]\n}"}]
        if match:
            json_str = match
            print("json_str : ", json_str)
            # report_demand_list = json.loads(json_str)

            chart_code_str = str(json_str).replace("\n", "")
            if len(chart_code_str) > 0:
                print("chart_code_str: ", chart_code_str)
                if base_util.is_json(chart_code_str):
                    report_demand_list = json.loads(chart_code_str)

                    print("report_demand_list: ", report_demand_list)

                    for jstr in report_demand_list:
                        if str(jstr).__contains__('echart_name') and str(jstr).__contains__(
                            'echart_code'):
                            base_content.append(jstr)
                else:
                    # String instantiated as object
                    report_demand_list = ast.literal_eval(chart_code_str)
                    print("report_demand_list: ", report_demand_list)
                    for jstr in report_demand_list:
                        if str(jstr).__contains__('echart_name') and str(jstr).__contains__(
                            'echart_code'):
                            base_content.append(jstr)
        logger.info(
                "from user:[{}".format(self.user_name) + "] , " + "，report_demand_list" + str(report_demand_list))

        bi_proxy = self.agent_instance_util.get_agent_bi_proxy()

        for img_str in base_content:
            echart_name = img_str.get('echart_name')
            echart_code = img_str.get('echart_code')

            if len(echart_code) > 0 and str(echart_code).__contains__('x'):
                is_chart = True
                print("echart_name : ", echart_name)
                # 格式化echart_code
                # if base_util.is_json(str(echart_code)):
                #     json_obj = json.loads(str(echart_code))
                #     echart_code = json.dumps(json_obj)

                re_str = await bi_proxy.run_echart_code(str(echart_code), echart_name)
                # base_mess.append(re_str)

        return "test_echrts_code"