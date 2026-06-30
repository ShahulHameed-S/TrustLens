from sqlalchemy.orm import Session
from app.repositories.role_repository import RoleRepository

class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.role_repo = RoleRepository(db)

    def ensure_default_roles(self):
        roles = ["admin", "user"]
        for role_name in roles:
            role = self.role_repo.get_by_name(role_name)
            if not role:
                self.role_repo.create_role(name=role_name)
