import asyncio
import random
from datetime import datetime, timezone

from app.services.providers.base import BaseAIProvider, AIProviderRequest, AIProviderResult


class MockProvider(BaseAIProvider):
    """Mock AI provider for development/testing/demo. Returns realistic Chinese educational content."""

    provider_name: str = "mock"

    async def run(self, request: AIProviderRequest) -> AIProviderResult:
        """Execute the mock AI call with a short artificial delay."""
        # Simulate network delay (0.5-1.5 seconds)
        await asyncio.sleep(random.uniform(0.5, 1.5))

        handlers = {
            "learning_diagnosis": self._handle_learning_diagnosis,
            "lesson_plan": self._handle_lesson_plan,
            "rubric_generation": self._handle_rubric_generation,
            "resource_recommendation": self._handle_resource_recommendation,
            "teaching_reflection": self._handle_teaching_reflection,
        }

        handler = handlers.get(request.scenario)
        if handler is None:
            return AIProviderResult(
                success=False,
                content=None,
                provider=self.provider_name,
                scenario=request.scenario,
                error_message=f"不支持的场景类型: {request.scenario}",
                requires_review=True,
                finished_at=datetime.now(timezone.utc),
            )

        try:
            content = handler(request.input_data)
            return AIProviderResult(
                success=True,
                content=content,
                provider=self.provider_name,
                scenario=request.scenario,
                metadata={"mock": True, "demo_mode": True},
                requires_review=True,
                finished_at=datetime.now(timezone.utc),
            )
        except Exception as e:
            return AIProviderResult(
                success=False,
                content=None,
                provider=self.provider_name,
                scenario=request.scenario,
                error_message=str(e),
                requires_review=True,
                finished_at=datetime.now(timezone.utc),
            )

    async def health_check(self) -> bool:
        """Mock provider is always available."""
        return True

    # ─── Scenario Handlers ────────────────────────────────────────────────────

    def _handle_learning_diagnosis(self, input_data: dict) -> dict:
        """学情诊断 - 班级画像与分层建议"""
        grade = input_data.get("grade", "七年级")
        subjects = input_data.get("subjects", ["语文", "数学", "地理"])

        return {
            "class_profile": (
                f"该{grade}班级整体学业水平处于中等偏上位置。在知识掌握层面，"
                f"大部分学生能够理解{ '、'.join(subjects[:2]) }的基础概念，"
                f"但在综合运用和跨学科迁移方面仍有提升空间。课堂参与度方面，"
                f"约65%的学生能够主动参与课堂讨论和小组活动，但仍有约20%的学生"
                f"在表达和协作方面需要更多支架。从学习习惯来看，班级整体学习态度端正，"
                f"但部分学生在自主探究和深度学习方面需要进一步引导。"
                f"前测数据显示，学生在单一学科知识点上的正确率达到72%，"
                f"但在跨学科综合题目上的正确率仅为48%，说明跨学科整合能力是本阶段重点培养方向。"
            ),
            "tiered_suggestions": [
                {
                    "tier": "A",
                    "description": "学科基础扎实，具备较好的探究和表达能力，能够独立完成跨学科任务",
                    "strategy": "提供开放性探究任务，鼓励担任小组长；引入拓展阅读和深度思考问题；引导帮助同伴学习，促进知识内化",
                },
                {
                    "tier": "B",
                    "description": "学科基础中等，在教师引导下能够完成跨学科任务，但自主性有待加强",
                    "strategy": "提供半结构化任务支架，如思维导图模板、问题链引导；加强学习方法指导；通过小组合作提升参与感和表达机会",
                },
                {
                    "tier": "C",
                    "description": "学科基础薄弱，在资料提取和表达组织方面需要更多支持",
                    "strategy": "提供结构化学习单和关键概念卡片；进行课前预习辅导；安排同伴互助；重点关注微小的进步并及时给予正向反馈",
                },
            ],
            "key_areas": [
                {
                    "area": "跨学科知识迁移",
                    "current_level": "部分学生能在教师引导下完成学科间的概念迁移",
                    "target": "大部分学生能够自主识别和运用多学科知识解决实际问题",
                },
                {
                    "area": "信息提取与分析",
                    "current_level": "约55%学生能够从图文材料中准确提取关键信息",
                    "target": "提升至75%以上，并能够进行简单的数据分析和推理",
                },
                {
                    "area": "合作与表达能力",
                    "current_level": "小组合作中约40%的发言集中在少数活跃学生",
                    "target": "每位学生都能在小组中承担角色并进行有效表达",
                },
                {
                    "area": "自主学习能力",
                    "current_level": "多数学生依赖教师布置的任务，主动探索意识不足",
                    "target": "培养学生制定个人学习目标和自我评估的习惯",
                },
            ],
        }

    def _handle_lesson_plan(self, input_data: dict) -> dict:
        """跨学科教学设计"""
        grade = input_data.get("grade", "七年级")
        subjects = input_data.get("subjects", ["地理", "生物", "语文"])
        topic = input_data.get("topic", "保护海洋，从我做起")
        lesson_count = input_data.get("lesson_count", 5)

        lessons = []
        for i in range(1, lesson_count + 1):
            lessons.append(
                {
                    "order": i,
                    "title": [
                        "海洋探秘：认识我们的蓝色星球",
                        "多学科视角看海洋生态",
                        "探究活动：身边的海洋问题",
                        "创意实践：设计环保方案",
                        "成果展示与反思评价",
                    ][i - 1] if i <= 5 else f"第{i}课时",
                    "objectives": [
                        [
                            f"了解海洋生态系统的组成和功能；能够在地图上标注中国主要海域",
                            f"分析海洋生物的食物链关系；理解海洋环境变化的生物学原因",
                            f"设计并实施小型调查研究；收集和分析数据",
                            f"综合运用所学知识设计环保方案；小组协作完成创意作品",
                            f"展示学习成果并进行同伴评价；反思学习过程和收获",
                        ][i - 1] if i <= 5 else f"第{i}课时的教学目标",
                    ][0],
                    "activities": [
                        [
                            "观看海洋纪录片片段，完成KWL表格；分组绘制海洋生态系统概念图；全班分享并汇总知识点",
                            "分小组从地理、生物、语文角度阅读材料；用思维导图建立学科联系；小组报告：海洋问题的多学科分析",
                            "设计调查问卷或观察记录表；开展校园/社区调查；整理数据并用图表呈现发现",
                            "头脑风暴环保方案；小组选择方向进行深入设计；制作海报、模型或PPT",
                            "各小组展示成果（5分钟/组）；同伴互评使用评价量规；个人撰写学习反思日志",
                        ][i - 1] if i <= 5 else f"第{i}课时的探究活动",
                    ][0],
                    "materials": [
                        [
                            "《蓝色星球》纪录片片段、世界地图、中国海域图、KWL表格、彩色便利贴",
                            "海洋生态主题阅读材料包（含地理、生物、语文学科视角）、A3纸、彩笔",
                            "调查问卷模板、观察记录表设计指南、数据统计表模板、相机/手机（用于拍照记录）",
                            "A2海报纸、彩笔、环保材料（可回收物）、平板/电脑（用于制作PPT）",
                            "评价量规打印件、反思日志模板、展示评分表、奖品（可选）",
                        ][i - 1] if i <= 5 else f"第{i}课时的教学材料",
                    ][0],
                    "duration": "45分钟",
                }
            )

        return {
            "theme": topic,
            "driving_question": (
                f"作为{grade}学生，我们如何从{ '、'.join(subjects) }的视角"
                f"理解{topic}这一议题，并通过实际行动为保护我们的海洋贡献一份力量？"
            ),
            "lessons": lessons,
            "cross_disciplinary_connections": {
                "地理": "海洋地理分布、中国海域特征、海洋资源分布、人类活动对海洋的影响",
                "生物": "海洋生态系统组成、食物链与食物网、生物多样性保护、环境污染对生物的影响",
                "语文": "阅读海洋主题的科普文章和文学作品、撰写调查报告和倡议书、进行口头报告",
                "数学": "数据统计与分析、图表制作、百分比计算（污染数据、生物数量变化等）",
                "信息科技": "利用网络搜集资料、使用工具制作展示作品、数据可视化",
            },
            "assessment_plan": (
                "采用过程性评价与终结性评价相结合的方式。"
                "过程性评价包括：课堂参与度观察、小组合作表现、KWL表格完成情况、"
                "思维导图质量、调查记录完整性。"
                "终结性评价包括：环保方案设计作品（海报/模型/PPT）、成果展示表现、"
                "个人反思日志。使用跨学科探究评价量规进行多维度评分，"
                "涵盖知识理解、探究能力、跨学科迁移、合作表达、创新思维等维度。"
                "教师评价占50%，同伴互评占30%，自我评价占20%。"
            ),
        }

    def _handle_rubric_generation(self, input_data: dict) -> dict:
        """评价量规生成"""
        objectives = input_data.get("objectives", ["理解海洋生态系统的组成", "完成跨学科调查与表达"])
        tasks = input_data.get("tasks", ["绘制概念图", "小组调查报告", "环保方案展示"])
        dimensions = input_data.get("dimensions", [
            "知识理解", "探究能力", "跨学科迁移", "合作表达", "问题解决", "创新思维", "社会责任"
        ])

        rubric_items = []
        dimension_templates = {
            "知识理解": {
                "weight": 15.0,
                "level_a": "能够准确、全面地阐述核心概念和原理，能够建立知识点之间的内在联系，并能举例说明",
                "level_b": "能够基本准确地阐述核心概念，在教师提示下能够建立知识点之间的联系",
                "level_c": "能够说出部分核心概念，但理解存在遗漏或偏差，知识点之间的联系不够清晰",
                "level_d": "对核心概念的理解有较大困难，需要进一步的个别辅导和基础巩固",
            },
            "探究能力": {
                "weight": 20.0,
                "level_a": "能够独立提出有深度的问题，设计合理的探究方案，系统收集和分析数据，得出有依据的结论",
                "level_b": "能够提出合理的探究问题，在教师指导下完成探究过程，数据收集和分析基本规范",
                "level_c": "能够在教师帮助下提出简单问题并参与探究活动，数据分析能力有待提高",
                "level_d": "需要较多的引导才能参与探究活动，在问题提出和数据分析方面需要大量支持",
            },
            "跨学科迁移": {
                "weight": 20.0,
                "level_a": "能够自主运用多个学科的知识和方法解决实际问题，跨学科整合有深度和创新性",
                "level_b": "能够在教师提示下运用2-3个学科的知识分析问题，建立基本的学科联系",
                "level_c": "能够识别问题涉及的学科领域，但学科间迁移和整合需要教师逐步引导",
                "level_d": "倾向于使用单一学科知识解决问题，跨学科迁移能力需要系统培养",
            },
            "合作表达": {
                "weight": 15.0,
                "level_a": "在小组中积极承担角色，有效倾听和回应同伴，表达清晰有条理，能使用多种形式呈现成果",
                "level_b": "能够参与小组合作，基本完成分配的任务，表达较为清晰",
                "level_c": "能够参与小组活动但主动性不足，表达需要更多组织和准备",
                "level_d": "在小组合作中存在明显困难，表达不够清晰，需要教师和同伴的特别支持",
            },
            "问题解决": {
                "weight": 10.0,
                "level_a": "能够识别问题的关键要素，提出多种解决方案并进行比较，有效实施方案并评估效果",
                "level_b": "能够分析问题并提出可行的解决方案，实施方案基本顺利",
                "level_c": "能够在帮助下分析问题，提出的解决方案比较单一",
                "level_d": "分析问题和提出方案存在较大困难，需要教师逐步引导",
            },
            "创新思维": {
                "weight": 10.0,
                "level_a": "能够提出新颖独特的观点或方案，善于从不同角度思考问题，敢于尝试非常规方法",
                "level_b": "能够偶尔提出有新意的想法，能够在一定程度上进行发散思维",
                "level_c": "创新意识初显，但更多依赖于模仿和常规思路",
                "level_d": "思维方式较为固定，需要更多创新思维训练和启发",
            },
            "社会责任": {
                "weight": 10.0,
                "level_a": "能够深入理解议题的社会意义，主动关注可持续发展，在行动中体现责任感和担当",
                "level_b": "能够理解议题的社会价值，在教师引导下关注环境和社会问题",
                "level_c": "对社会和环境问题有一定认知，但深度和主动性有待加强",
                "level_d": "对社会和环境问题的理解较为表面，需要更多情境体验和引导",
            },
        }

        for dim in dimensions:
            if dim in dimension_templates:
                template = dimension_templates[dim]
                rubric_items.append({
                    "dimension": dim,
                    "weight": template["weight"],
                    "level_a": template["level_a"],
                    "level_b": template["level_b"],
                    "level_c": template["level_c"],
                    "level_d": template["level_d"],
                })

        return {
            "name": f"跨学科主题学习评价量规 - {tasks[0] if tasks else '综合任务'}",
            "description": (
                f"本量规用于评价学生在跨学科主题学习活动中的综合表现，"
                f"涵盖{ '、'.join(dimensions) }等维度。"
                f"采用四级评价体系（A-优秀/B-良好/C-合格/D-需改进），"
                f"适用于教师评价、同伴互评和学生自评。"
            ),
            "items": rubric_items,
            "scoring_guide": {
                "A": "总分90分及以上：学生展现出卓越的跨学科学习能力",
                "B": "总分75-89分：学生展现出良好的跨学科学习能力",
                "C": "总分60-74分：学生基本达成跨学科学习目标",
                "D": "总分60分以下：学生需要进一步支持以达成学习目标",
            },
        }

    def _handle_resource_recommendation(self, input_data: dict) -> dict:
        """资源推荐"""
        topic = input_data.get("topic", "保护海洋")
        subjects = input_data.get("subjects", ["地理", "生物"])
        grade = input_data.get("grade", "七年级")
        textbook_version = input_data.get("textbook_version", "人教版")

        resources = [
            {
                "title": f"《探索海洋世界》科普系列视频",
                "type": "video",
                "description": f"由中国科学院海洋研究所制作的海洋科普系列，涵盖海洋地理、海洋生物、海洋环境等内容，共10集，每集15分钟。语言通俗易懂，适合{grade}学生观看。",
                "suggested_use": "可在课堂教学导入环节使用，或布置为课前预习任务。建议在'海洋探秘'课时播放第1-3集。",
                "relevance_score": 95,
                "url": "https://example.com/ocean-exploration-videos",
            },
            {
                "title": f"《{topic}主题活动手册》",
                "type": "document",
                "description": f"包含{topic}主题的项目式学习活动设计方案，有详细的任务链、评价量规和学生工作单。与{textbook_version}教材内容衔接紧密。",
                "suggested_use": "作为教师备课参考和学生活动指南。可直接选用其中的调查问卷模板和数据记录表。",
                "relevance_score": 90,
            },
            {
                "title": "国家海洋局《2025年中国海洋环境状况公报》",
                "type": "document",
                "description": "官方发布的海洋环境数据，包含水质、生物多样性、污染状况等方面的权威数据，可用于学生数据分析和探究活动。",
                "suggested_use": "适合作为'探究活动：身边的海洋问题'课时的数据来源。教师可提取关键数据和图表供学生分析讨论。",
                "relevance_score": 85,
                "url": "https://example.com/ocean-report-2025",
            },
            {
                "title": f"《海洋中的食物链》互动模拟课件",
                "type": "software",
                "description": f"一款基于HTML5的互动课件，学生可以拖拽海洋生物构建食物链，观察生态系统变化。支持{grade}水平，操作简便。",
                "suggested_use": "可用于生物学科的探究环节，让学生在动手操作中理解食物链和生态平衡的概念。建议分组使用，每组一台设备。",
                "relevance_score": 88,
                "url": "https://example.com/food-chain-sim",
            },
            {
                "title": f"《从海洋说起》跨学科阅读材料包",
                "type": "document",
                "description": f"精心编选的阅读材料合集，包含科普文章、新闻报道、文学作品节选等，每篇配有阅读指引和思考问题。覆盖{'、'.join(subjects)}等学科视角。",
                "suggested_use": "作为各课时阅读环节的核心材料。教师可根据学生分层选择不同难度的材料。A层学生阅读全部材料并完成拓展思考。",
                "relevance_score": 92,
            },
            {
                "title": f"沿海城市海洋环保实践案例集",
                "type": "document",
                "description": f"收录了青岛、厦门、三亚等沿海城市学校和社区开展海洋环保实践的案例，每个案例包括问题背景、行动方案、实施效果和经验反思。",
                "suggested_use": "在'创意实践：设计环保方案'课时前让学生阅读参考案例，激发灵感。可作为B层和C层学生的重要支架。",
                "relevance_score": 80,
            },
            {
                "title": "海洋主题虚拟实境（VR）体验资源",
                "type": "software",
                "description": "提供海底珊瑚礁、深海热液喷口等场景的虚拟实境体验，学生可360度观察海洋生态系统。需要学校VR设备或平板电脑支持。",
                "suggested_use": "适合作为拓展体验活动。如果没有VR设备，可使用桌面端360度全景图片代替。建议安排在'海洋探秘'课时。",
                "relevance_score": 75,
            },
            {
                "title": f"《跨学科教学评价量规模板库》",
                "type": "document",
                "description": f"提供多种跨学科主题学习的评价量规模板，涵盖探究报告、口头展示、科学海报、项目方案等多种任务类型。可直接修改使用。",
                "suggested_use": "供教师参考和修改。可与AI量规生成功能配合使用，教师生成量规后与模板对比调整。",
                "relevance_score": 78,
            },
        ]

        return {"resources": resources, "total": len(resources), "note": f"以上资源基于{textbook_version}{grade}教材内容推荐，教师可根据实际教学需要筛选和调整。资源已标注建议使用场景，其中部分为外部链接，建议提前检查可访问性。"}

    def _handle_teaching_reflection(self, input_data: dict) -> dict:
        """教学反思"""
        evaluation_summary = input_data.get("evaluation_summary", "多数学生达到了基本的跨学科学习目标")
        process_observations = input_data.get("process_observations", "课堂参与度较好")

        return {
            "strengths": [
                {
                    "point": "跨学科教学设计的连贯性较好",
                    "detail": "从海洋认知到问题分析再到方案设计和成果展示，各课时之间的衔接自然流畅。学生在学习过程中能够感受到知识的内在逻辑，学习目标逐层递进。",
                    "evidence": "89%的学生能够在反思日志中清晰描述每个课时的学习内容和相互联系。",
                },
                {
                    "point": "小组合作学习效果显著",
                    "detail": "通过分组活动和角色分配，学生在协作中学会了倾听、表达和协调。特别是A层学生担任组长后，责任感明显增强，B层和C层学生在同伴帮助下参与度提升。",
                    "evidence": "课堂观察记录显示，小组合作环节的学生参与率从第一次课的62%提升到第五次课的91%。",
                },
                {
                    "point": "驱动问题激发了学生的探究兴趣",
                    "detail": "贴近生活的驱动问题让学生感受到了学习的现实意义。学生在设计方案时展现了超出预期的创造力，部分小组主动查阅了课外资料。",
                    "evidence": "75%的学生在反思中提到'想了解更多关于海洋保护的知识'，部分小组主动提出了延伸探究方向。",
                },
            ],
            "improvements": [
                {
                    "point": "跨学科整合深度有待加强",
                    "detail": "虽然教学设计覆盖了多个学科，但在实际教学中，学生更多是在地理和生物两个学科之间建立联系，语文和数学的整合还不够自然和深入。",
                    "suggestion": "下一轮教学时，可以在语文课上专门安排一次海洋主题的写作课，在数学课上指导学生用数学方法分析环境污染数据，使学科整合更加自然。",
                },
                {
                    "point": "C层学生的支架需要更加精准",
                    "detail": "虽然提供了结构化的学习材料和同伴互助，但部分C层学生在'设计环保方案'环节仍然感到困难，提出的方案比较笼统。",
                    "suggestion": "为C层学生提供更具体的方案模板和案例参考，减少开放性任务的不确定性。可以在课前进行迷你工作坊，帮助学生掌握设计思维的基本步骤。",
                },
                {
                    "point": "评价反馈的及时性不足",
                    "detail": "由于班级人数较多，教师在过程性评价中对每个学生的及时反馈不够充分。部分学生反映在提交作品后等待反馈的时间偏长。",
                    "suggestion": "引入更多同伴互评环节，制定更简洁的同伴评价表格。利用课间或自习时间进行快速反馈。考虑使用学习平台辅助收集和反馈学生作业。",
                },
            ],
            "student_engagement": {
                "overall": "学生整体参与度较高，特别是在动手实践和成果展示环节表现积极。",
                "highlights": "角色扮演和方案设计环节激发了学生的创造力；小组合作中出现了自发的同伴教学行为。",
                "concerns": "约15%的学生在独立阅读和写作环节表现出畏难情绪；个别学生在小组合作中处于边缘位置。",
                "data_points": {
                    "主动发言率": "从30%提升至55%",
                    "任务按时完成率": "87%",
                    "课后主动查阅资料的比例": "42%",
                    "对课程满意度的自我评价": "4.3/5.0",
                },
            },
            "next_steps": [
                {
                    "action": "设计跨学科写作和数据分析专项活动",
                    "rationale": "加强语文和数学在跨学科项目中的有机整合",
                    "timeline": "下一单元教学前完成设计",
                    "priority": "high",
                },
                {
                    "action": "开发分层学习支架工具包",
                    "rationale": "为不同层次学生提供精准的学习支持",
                    "timeline": "未来两周内完成初稿",
                    "priority": "high",
                },
                {
                    "action": "建立同伴互评常态化机制",
                    "rationale": "提高反馈的及时性和学生元认知能力",
                    "timeline": "下节课开始试行",
                    "priority": "medium",
                },
                {
                    "action": "收集学生的深度学习案例",
                    "rationale": "积累优秀作品用于今后的教学示范和教研交流",
                    "timeline": "本学期持续进行",
                    "priority": "low",
                },
            ],
        }
