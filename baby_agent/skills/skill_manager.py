from typing import Dict, Type, List

class Skill:
    def __init__(self):
        self.name = ""
        self.description = ""
    
    def run(self, *args, **kwargs):
        pass

class SkillManager:
    def __init__(self):
        self.skills: Dict[str, Skill] = {}
    
    def register_skill(self, skill: Skill):
        """注册技能"""
        self.skills[skill.name] = skill
    
    def get_skill(self, name: str) -> Skill:
        """获取技能"""
        return self.skills.get(name)
    
    def list_skills(self) -> List[str]:
        """列出所有技能"""
        return list(self.skills.keys())
