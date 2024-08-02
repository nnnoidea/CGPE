
entity_chain_prompt = """
请抽取文本中的实体。
文本：请问李明老师教授哪些课程？
实体：(李明, 课程)
文本：看过数据结构第1章第3节的学生中包不包括赵尔？
实体：(数据结构第1章第3节, 学生, 赵尔)
文本：张华老师的课程里关于数据组织的视频有哪些？
实体：(张华, 课程, 数据组织, 视频)
文本：%s
实体："""



info_match_prompt = """
请判断句子中的信息跟目标实体的匹配程度，并打分，最低0分，最高10分。目标实体的格式为(标签, 实体)。
句子：'李明老师教会了张三什么是向量吗？'
信息：['李明', '向量']
目标实体：('概念', '张量')
答：'李明'是个老师，跟目标实体不匹配，打分0分。
'向量'跟目标实体很匹配，打分9分。
句子：'赵珊看了艺术与美第2章第1节吗？'
信息：['赵珊', '艺术与美第2章第1节']
目标实体：('课程', '数据结构')
答：'赵珊'是个人，跟课程不匹配，打分0分。
'艺术与美第2章第1节'跟数据结构不匹配，打分0分。
句子：{}
信息：{}
目标实体：{}
答："""

select_node_prompt = """
请判断每一个候选实体与句子中信息的相关度，并打分，最低0分，最高10分。候选实体的格式为：(标签, 实体名)。
句子：'李明老师教会了张三什么是向量吗？'
信息：['李明', '向量']
候选实体：[('概念', '张量'), ('课程', '艺术与美')]
答：('概念', '张量')可能跟'向量'相关，打分7分。
('课程', '艺术与美')跟句子中信息无关相关，打分0分。
句子：{}
信息：{}
候选实体：{}
答："""
prune_prompt = """
请判断当前实体的关联节点中，哪个跟句子中的目标信息更匹配，并打分，最低0分，最高10分。关联节点的格式为(关系, 标签)。
句子：'李明老师教了张三数据结构课吗？'
目标信息：['张三', '数据结构课']
当前实体：('教师', '李明')
关联节点：[('教师-课程', '课程'), ('教师-用户', '用户'), ('教师-学校', '学校')]
答：('教师-课程', '课程')跟'数据结构课'更匹配，打分9分。
('教师-用户', '用户')可能跟'张三'匹配，打分5分。
('教师-学校', '学校')跟目标信息不匹配，打分0分。
句子：{}
目标信息：{}
当前实体：{}
关联节点：{}
答："""

answer_prompt = """
请根据提供的三元组回答问题。三元组的格式为(实体1, 关系, 实体2)。
问题：张三是不是开了神秘学这门课？
三元组：('张三', '教师-课程', '神秘学'), ('张三', '教师-课程', '人力学')
答：是，三元组表明张三是神秘学这门课的教师。
问题：赵益是不是看了Java程序设计第9章第3节？
三元组：（'赵益', '用户-课程', '数据结构')
答：否，赵益跟Java程序设计第9章第3节无关。
问题：向量是哪些课程的概念？
三元组：('数据结构', '课程-概念', '向量'), ('向量', '课程-概念', '计算几何')
答：数据结构，计算几何
问题：{}
三元组：{}
答："""