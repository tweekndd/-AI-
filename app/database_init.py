"""
数据库初始化脚本
运行此脚本即可创建所有数据库表
"""
from app.database import init_db


def main():
    """初始化数据库"""
    print("正在初始化数据库...")
    init_db()
    print("数据库初始化完成！")


if __name__ == "__main__":
    main()
