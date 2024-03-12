# Задание №6
# Необходимо создать базу данных для интернет-магазина. База данных должна
# состоять из трех таблиц: товары, заказы и пользователи. Таблица товары должна
# содержать информацию о доступных товарах, их описаниях и ценах. Таблица
# пользователи должна содержать информацию о зарегистрированных
# пользователях магазина. Таблица заказы должна содержать информацию о заказах, сделанных пользователями.
# ○ Таблица пользователей должна содержать следующие поля: id (PRIMARY KEY), имя, фамилия, адрес электронной почты и пароль.
# ○ Таблица товаров должна содержать следующие поля: id (PRIMARY KEY), название, описание и цена.
# ○ Таблица заказов должна содержать следующие поля: id (PRIMARY KEY), id
# пользователя (FOREIGN KEY), id товара (FOREIGN KEY), дата заказа и статус заказа.
# Создайте модели pydantic для получения новых данных и
# возврата существующих в БД для каждой из трёх таблиц (итого шесть моделей).
# Реализуйте CRUD операции для каждой из таблиц через создание маршрутов, REST API (итого 15 маршрутов).
# ○ Чтение всех
# ○ Чтение одного
# ○ Запись
# ○ Изменение
# ○ Удаление


from datetime import datetime
from random import randint
from faker import Faker
from fastapi import FastAPI
import databases
import sqlalchemy
from pydantic import BaseModel, Field
from typing import List

DATABASE_URL = "sqlite:///mydatabase_for_task6.db"
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

products = sqlalchemy.Table(
    "products",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("title", sqlalchemy.String),
    sqlalchemy.Column("description", sqlalchemy.String),
    sqlalchemy.Column("price", sqlalchemy.Integer),
)

users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String),
    sqlalchemy.Column("surname", sqlalchemy.String),
    sqlalchemy.Column("email", sqlalchemy.String),
    sqlalchemy.Column("password", sqlalchemy.String)
)

orders = sqlalchemy.Table(
    "orders",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, foreign_key="users.id"),
    sqlalchemy.Column("product_id", sqlalchemy.Integer, foreign_key="products.id"),
    sqlalchemy.Column("date", sqlalchemy.String),
    sqlalchemy.Column("status", sqlalchemy.String)

)

engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
metadata.create_all(engine)


class ProductIn(BaseModel):
    title: str = Field(max_length=100)
    description: str = Field(max_length=1000)
    price: int = Field(ge=0)


class Product(ProductIn):
    id: int


class UserIn(BaseModel):
    name: str = Field(max_length=100)
    surname: str = Field(max_length=100)
    email: str = Field(max_length=100)
    password: str = Field(max_length=100)


class User(UserIn):
    id: int


class OrderIn(BaseModel):
    user_id: int
    product_id: int
    date: datetime = Field(default_factory=datetime.now)
    status: str = Field(default="pending")


class Order(OrderIn):
    id: int


app = FastAPI()
fake = Faker('ru_RU')


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get('/fake_users/{count}')
async def create_users(count: int):
    for _ in range(count):
        query = users.insert().values(
            name=fake.first_name(),
            surname=fake.last_name(),
            email=fake.email(),
            password=fake.password()
        )
        await database.execute(query)
    return {'message': f'{count} fake users create'}


@app.get('/fake_products/{count}')
async def create_products(count: int):
    for i in range(count):
        query = products.insert().values(
            title=f'title_{i}',
            description=fake.bs(),
            price=randint(100, 1000)
        )
        await database.execute(query)
    return {'message': f'{count} fake products create'}


@app.get('/fake_orders/{count}')
async def create_orders(count: int):
    for _ in range(count):
        query = orders.insert().values(
            user_id=randint(1, 10),
            product_id=randint(1, 10),
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            status=fake.random_element(elements=('pending', 'processing', 'shipped', 'delivered', 'cancelled'))
        )
        await database.execute(query)
    return {'message': f'{count} fake orders create'}


@app.get('/products/', response_model=List[Product])
async def read_products():
    query = products.select()
    return await database.fetch_all(query)


@app.get('/products/{product_id}', response_model=Product)
async def read_product(product_id: int):
    query = products.select().where(products.c.id == product_id)
    return await database.fetch_one(query)


@app.post('/products/', response_model=Product)
async def create_product(product: ProductIn):
    query = products.insert().values(**product.dict())
    last_record_id = await database.execute(query)
    return {**product.dict(), "id": last_record_id}


@app.put('/products/{product_id}', response_model=Product)
async def update_product(product_id: int, product: ProductIn):
    query = products.update().where(products.c.id == product_id).values(**product.dict())
    await database.execute(query)
    return {**product.dict(), "id": product_id}


@app.delete('/products/{product_id}')
async def delete_product(product_id: int):
    query = products.delete().where(products.c.id == product_id)
    await database.execute(query)
    return {'message': 'Product deleted'}


@app.get('/users/', response_model=List[User])
async def read_users():
    query = users.select()
    return await database.fetch_all(query)


@app.get('/users/{user_id}', response_model=User)
async def read_user(user_id: int):
    query = users.select().where(users.c.id == user_id)
    return await database.fetch_one(query)


@app.post('/users/', response_model=User)
async def create_user(user: UserIn):
    query = users.insert().values(**user.dict())
    last_record_id = await database.execute(query)
    return {**user.dict(), "id": last_record_id}


@app.put('/users/{user_id}', response_model=User)
async def update_user(user_id: int, user: UserIn):
    query = users.update().where(users.c.id == user_id).values(**user.dict())
    await database.execute(query)
    return {**user.dict(), "id": user_id}


@app.delete('/users/{user_id}')
async def delete_user(user_id: int):
    query = users.delete().where(users.c.id == user_id)
    await database.execute(query)
    return {'message': 'User deleted'}


@app.get('/orders/', response_model=List[Order])
async def read_orders():
    query = orders.select()
    return await database.fetch_all(query)


@app.get('/orders/{order_id}', response_model=Order)
async def read_order(order_id: int):
    query = orders.select().where(orders.c.id == order_id)
    return await database.fetch_one(query)


@app.post('/orders/', response_model=Order)
async def create_order(order: OrderIn):
    query = orders.insert().values(**order.dict())
    last_record_id = await database.execute(query)
    return {**order.dict(), "id": last_record_id}


@app.put('/orders/{order_id}', response_model=Order)
async def update_order(order_id: int, order: OrderIn):
    query = orders.update().where(orders.c.id == order_id).values(**order.dict())
    await database.execute(query)
    return {**order.dict(), "id": order_id}


@app.delete('/orders/{order_id}')
async def delete_order(order_id: int):
    query = orders.delete().where(orders.c.id == order_id)
    await database.execute(query)
    return {'message': 'Order deleted'}
