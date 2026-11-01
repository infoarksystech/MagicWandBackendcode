from app.routers import  orders, playground, products, categories, carts, projects, users, auth, accounts, wishlist,prompt,project_update,image_style_router,settings,overlay,gallery,tag,organization,org_user # type: ignore
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

description = """
Welcome to the E-commerce API! 🚀

This API provides a comprehensive set of functionalities for managing your e-commerce platform.

Key features include:

- **Crud**
	- Create, Read, Update, and Delete endpoints.
- **Search**
	- Find specific information with parameters and pagination.
- **Auth**
	- Verify user/system identity.
	- Secure with Access and Refresh tokens.
- **Permission**
	- Assign roles with specific permissions.
	- Different access levels for User/Admin.
- **Validation**
	- Ensure accurate and secure input data.


For any inquiries, please contact:

* Github: https://github.com/aliseyedi01
"""


app = FastAPI(
    description=description,
    title="E-commerce API",
    version="1.0.0",
    contact={
        "name": "Magicwand",
        "url": "https://github.com/aliseyedi01",
    },
    swagger_ui_parameters={
        "syntaxHighlight.theme": "monokai",
        "layout": "BaseLayout",
        "filter": True,
        "tryItOutEnabled": True,
        "onComplete": "Ok"
    },
)


@app.get("/test", tags=["Health Check"])
def test_api():
    return {
        "status": "ok",
        "message": "Test API is working. This code is running on the server.",
    }


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "..", "assets")

app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (change to specific domains if needed)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

app.include_router(products.router)
app.include_router(categories.router)
app.include_router(carts.router)
app.include_router(users.router)
app.include_router(accounts.router)
app.include_router(auth.router)
app.include_router(wishlist.router)
app.include_router(orders.router)
app.include_router(projects.router)
app.include_router(prompt.router)
app.include_router(project_update.router)
app.include_router(image_style_router.router)
app.include_router(settings.router)
app.include_router(overlay.router)
app.include_router(gallery.router)
app.include_router(tag.router)
app.include_router(playground.router)
app.include_router(organization.router)
app.include_router(org_user.router)
#0bB-pIFc8Tjc8Jb1DCz3bwJQUELFdNhzhJ24sXhKu37k5JrmpPIxUwzp-Hw1zFL61-ZQosJygegFUPWxEWuPyA
