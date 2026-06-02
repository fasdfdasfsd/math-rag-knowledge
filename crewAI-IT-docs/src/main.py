#!/usr/bin/env python3
"""
多智能体需求文档生成器入口
=============================
- 解析命令行参数（主题、输出路径、知识库、记忆、迭代、重试）
- 调度 CrewAI 流水线顺序执行 5 个任务
- 支持质量迭代：解析 ECC 输出的评分，低于阈值自动反馈重生成
- 完善的异常处理与结构化日志

用法示例：
  python main.py --topic "在线图书管理系统" --output output/doc.md
  python main.py --topic "..." --max-iterations 3 --retry 2
"""
import argparse
import os
import re
import sys
import time
from pathlib import Path

# 确保 src 目录在 sys.path 中，支持直接运行
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
from crewai import Crew, Process
from agents import (
    requirement_analyst, system_architect, technical_writer,
    claude_code_reviewer, ecc_controller
)
from tasks import get_tasks
from utils.logger import setup_logger

# 加载 .env 文件中的环境变量
load_dotenv()
logger = setup_logger(__name__)

# ECC 评分阈值：低于此分将触发重新生成
QUALITY_THRESHOLD = 8


def extract_score_and_issues(document: str):
    """
    从文档末尾提取 ECC 质量评分和问题列表。
    :param document: 完整的文档文本
    :return: (score, issues) — score 为 int 或 None，issues 为 str
    """
    score = None
    issues = ""
    match = re.search(r'### ECC_QUALITY_SCORE:\s*(\d+)/10', document)
    if match:
        score = int(match.group(1))
    issues_match = re.search(r'### ECC_ISSUES:\s*(.+)', document)
    if issues_match:
        issues = issues_match.group(1).strip()
    return score, issues


def run_crew(
    topic: str,
    output_path: str,
    knowledge_dir: str = None,
    memory_file: str = None,
    max_retries: int = 1,
    max_iterations: int = 1
):
    """
    执行 CrewAI 流水线，支持质量迭代。
    :param topic: 项目主题
    :param output_path: 输出文件路径
    :param knowledge_dir: 知识库目录（可选）
    :param memory_file: 全局记忆文件路径（可选）
    :param max_retries: 单次生成的最大重试次数
    :param max_iterations: 最大迭代次数（≥2 时启用质量闭环）
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    current_topic = topic
    final_doc = ""

    for iteration in range(1, max_iterations + 1):
        logger.info(f"======== 迭代 {iteration}/{max_iterations} ========")
        success = False

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"尝试 {attempt}/{max_retries}，主题：{current_topic[:120]}...")
                start_time = time.time()

                # 获取任务列表
                tasks = get_tasks(knowledge_dir=knowledge_dir, memory_file=memory_file)

                # 组建 Crew
                crew = Crew(
                    agents=[
                        requirement_analyst, system_architect, technical_writer,
                        claude_code_reviewer, ecc_controller
                    ],
                    tasks=tasks,
                    process=Process.sequential,
                    memory=False,   # 关闭内置记忆，使用自定义全局记忆
                    verbose=True
                )

                # 启动流水线
                result = crew.kickoff(inputs={"topic": current_topic})
                final_doc = str(result)

                # 记录各任务输出长度（辅助成本追踪）
                for task in tasks:
                    if hasattr(task, 'output') and task.output:
                        raw = task.output.raw
                        if raw:
                            logger.info(f"任务 {task.name} 输出长度：{len(raw)} 字符")
                        else:
                            logger.warning(f"任务 {task.name} 输出为空")
                    else:
                        logger.warning(f"任务 {task.name} 无输出记录")

                elapsed = time.time() - start_time
                logger.info(f"本次生成耗时 {elapsed:.1f}s，文档总长度：{len(final_doc)} 字符")

                # 质量迭代检查
                if max_iterations > 1:
                    score, issues = extract_score_and_issues(final_doc)
                    if score is not None:
                        logger.info(f"ECC 质量评分：{score}/10")
                        if score < QUALITY_THRESHOLD and iteration < max_iterations:
                            logger.info(
                                f"评分低于阈值 {QUALITY_THRESHOLD}，"
                                f"准备下一次迭代。主要问题：{issues}"
                            )
                            # 构造反馈主题，注入问题上下文
                            current_topic = (
                                f"{topic}\n\n[系统反馈] 上一版本文档存在以下问题：{issues}\n"
                                "请针对上述问题进行修正，重新生成完整的需求规格说明书。"
                            )
                            break  # 跳出重试循环，进入下一次迭代
                    else:
                        logger.warning("未找到质量评分标记，视为通过")

                # 保存结果
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(final_doc)
                logger.info(f"文档已保存至 {output_path}")
                success = True
                break  # 成功跳出重试循环

            except Exception as e:
                logger.error(f"尝试 {attempt} 失败：{str(e)}", exc_info=True)
                if attempt == max_retries:
                    logger.error("已达最大重试次数。")
                    raise
                else:
                    logger.info("等待 5 秒后重试...")
                    time.sleep(5)

        if success:
            break  # 跳出迭代循环
        else:
            logger.warning(f"迭代 {iteration} 未生成满意结果，继续下一迭代")
    else:
        # 所有迭代完成，保存最后一次结果
        logger.warning("所有迭代完成，可能未达到质量阈值，保存最后一次结果。")
        if final_doc:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(final_doc)
        else:
            raise RuntimeError("所有迭代均失败，未生成任何文档。")


def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(
        description="AI-Docs：多智能体需求文档生成器（IEEE 830 标准）"
    )
    parser.add_argument("--topic", required=True, help="项目主题描述")
    parser.add_argument(
        "--output",
        default="output/需求规格说明书.md",
        help="输出文件路径（默认：output/需求规格说明书.md）"
    )
    parser.add_argument("--knowledge-dir", default=None, help="知识库目录路径")
    parser.add_argument("--memory-file", default=None, help="全局记忆文件路径")
    parser.add_argument(
        "--retry", type=int, default=1,
        help="单次生成失败后的重试次数（默认 1）"
    )
    parser.add_argument(
        "--max-iterations", type=int, default=1,
        help="质量迭代次数，>1 时自动根据 ECC 评分重新生成（默认 1）"
    )

    args = parser.parse_args()

    try:
        run_crew(
            topic=args.topic,
            output_path=args.output,
            knowledge_dir=args.knowledge_dir,
            memory_file=args.memory_file,
            max_retries=args.retry,
            max_iterations=args.max_iterations
        )
        print(f"✅ 需求规格说明书已生成：{args.output}")
    except Exception as e:
        print(f"❌ 生成失败：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()