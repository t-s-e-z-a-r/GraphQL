import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
import pymongo
from typing import List, Optional
from bson import ObjectId

# client = pymongo.MongoClient('localhost', 27017, username='base', password='example')
client = pymongo.MongoClient('mongo', 27017, username='root', password='example')
db = client.local
users_collection = db.users
skills_collection = db.skills 

@strawberry.type
class Skill:
    id: strawberry.ID
    name: str
    description: str

@strawberry.type
class User:
    id: strawberry.ID
    name: str
    age: int
    height: int
    weight: int
    skills: List[strawberry.ID]

@strawberry.type
class Query:
    @strawberry.field
    def users(self) -> List[User]:
        users = []
        for user_data in users_collection.find():
            user = User(
                id=str(user_data["_id"]),
                name=user_data["name"],
                age=user_data["age"],
                height=user_data["height"],
                weight=user_data["weight"],
                skills=[str(skill_id) for skill_id in user_data["skills"]]
            )
            users.append(user)
        return users

    @strawberry.field
    def user(self, id: strawberry.ID) -> User:
        user_data = users_collection.find_one({"_id": ObjectId(id)})
        if user_data:
            return User(
                id=str(user_data["_id"]),
                name=user_data["name"],
                age=user_data["age"],
                height=user_data["height"],
                weight=user_data["weight"],
                skills=[str(skill_id) for skill_id in user_data["skills"]]
            )
        return None

    @strawberry.field
    def skills(self) -> List[Skill]:
        return [
            Skill(id=str(skill["_id"]), name=skill["name"], description=skill["description"])
            for skill in skills_collection.find()
        ]

    @strawberry.field
    def skill(self, id: strawberry.ID) -> Skill:
        skill_data = skills_collection.find_one({"_id": ObjectId(id)})
        if skill_data:
            return Skill(id=str(skill_data["_id"]), name=skill_data["name"], description=skill_data["description"])
        return None

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, name: str, age: int, height: int, weight: int, skillIds: List[strawberry.ID]) -> User:
        user_data = {
            "name": name,
            "age": age,
            "height": height,
            "weight": weight,
            "skills": [ObjectId(skill_id) for skill_id in skillIds]
        }
        users_collection.insert_one(user_data)
        return User(
            id=str(user_data["_id"]),
            name=name,
            age=age,
            height=height,
            weight=weight,
            skills=skillIds
        )

    @strawberry.mutation
    def create_skill(self, name: str, description: str) -> Skill:
        skill_data = {"name": name, "description": description}
        skills_collection.insert_one(skill_data)
        return Skill(id=str(skill_data["_id"]), name=name, description=description)

    @strawberry.mutation
    def update_user(self, id: strawberry.ID, name: Optional[str] = None, age: Optional[int] = None, height: Optional[int] = None, weight: Optional[int] = None, skillIds: Optional[List[strawberry.ID]] = None) -> User:
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if age is not None:
            update_data["age"] = age
        if height is not None:
            update_data["height"] = height
        if weight is not None:
            update_data["weight"] = weight
        if skillIds is not None:
            update_data["skills"] = [ObjectId(skill_id) for skill_id in skillIds]

        users_collection.update_one({"_id": ObjectId(id)}, {"$set": update_data})
        updated_user = users_collection.find_one({"_id": ObjectId(id)})
        return User(
            id=str(updated_user["_id"]),
            name=updated_user["name"],
            age=updated_user["age"],
            height=updated_user["height"],
            weight=updated_user["weight"],
            skills=[str(skill_id) for skill_id in updated_user["skills"]]
        )

    @strawberry.mutation
    def delete_user(self, id: strawberry.ID) -> User:
        deleted_user = users_collection.find_one_and_delete({"_id": ObjectId(id)})
        return User(
            id=str(deleted_user["_id"]),
            name=deleted_user["name"],
            age=deleted_user["age"],
            height=deleted_user["height"],
            weight=deleted_user["weight"],
            skills=[str(skill_id) for skill_id in deleted_user["skills"]]
        )

schema = strawberry.Schema(query=Query, mutation=Mutation)

graphql_app = GraphQLRouter(schema)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
