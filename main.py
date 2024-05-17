import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
import pymongo
from typing import List
import collections
from bson import ObjectId


client = pymongo.MongoClient('localhost', 27017, username='base', password='example')
db = client.local
users_collection = db.users
skills_collection = db.skills  # Renamed to avoid confusion
 
@strawberry.type
class Skill:
    _id: int
    name: str
    description: str

@strawberry.type
class User:
    _id: int 
    name: str
    age: int
    height: int
    weight: int
    skills: List[str]

    @strawberry.field
    def userSkills(self) -> List[Skill]: 
        user_skills = []
        for skill_id in self.skills:
            for skill in skills_collection.find({"_id": skill_id}):
                user_skills.append(Skill(_id=skill["_id"], name=skill["name"], description=skill["description"]))
        return user_skills    
    
@strawberry.type
class Query:
    @strawberry.field
    def users(self) -> List[User]:
        users = []
        for user_data in users_collection.find():
            user = User(_id=user_data["_id"], name=user_data["name"], age=user_data["age"], height=user_data["height"], weight=user_data["weight"], skills=user_data["skills"])
            user_skills = user.userSkills()
            users.append(user)
        return users

    
    @strawberry.field
    def user(self, id: int) -> User:
        user_data = users_collection.find_one({"_id": id})
        if user_data:
            return User(**{x: user_data[x] for x in User.__annotations__ })
        else:
            return None

    @strawberry.field
    def skills(self) -> List[Skill]:
        return [Skill(**skill) for skill in skills_collection.find()]

    @strawberry.field
    def skill(self, id: int) -> Skill:
        skill_data = skills_collection.find_one({"_id": id})
        if skill_data:
            return Skill(**skill_data)
        else:
            return None
        
@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, name: str, age: int, height: int, weight: int, skillIds: List[str]) -> User:
        user_data = {"name": name, "age": age, "height": height, "weight": weight, "skills": skillIds}
        print(user_data)
        users_collection.insert_one(user_data)
        return User(**user_data)

    @strawberry.mutation
    def create_skill(self, name: str, description: str) -> Skill:
        skill = {"name": name, "description": description}
        skills_collection.insert_one(skill)
        return Skill(**skill)

    @strawberry.mutation
    def update_user(self, id: int, name: str, age: int, height: int, weight: int) -> User:
        users_collection.update_one({"id": id}, {"$set": {"name": name, "age": age, "height": height, "weight": weight}})
        updated_user = users_collection.find_one({"id": id})
        # del updated_user["_id"]
        return User(**updated_user)

    @strawberry.mutation
    def delete_user(self, id: int) -> User:
        deleted_user = users_collection.find_one_and_delete({"id": id})
        # del deleted_user["_id"]
        return User(**deleted_user)


schema = strawberry.Schema(query=Query, mutation=Mutation)

graphql_app = GraphQLRouter(schema)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
