from sqlalchemy import JSON, Boolean, Column, Integer, String,Table, ForeignKey, DateTime,Float, ARRAY, Enum ,Text
from sqlalchemy.sql.expression import text
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy import DateTime, func
from datetime import datetime, timedelta
from sqlalchemy.orm import relationship
from sqlalchemy.orm import relationship
from app.db.database import Base



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    
    # ✅ New field
    phone = Column(String(15), unique=True, nullable=True)  # allow null for existing users

    is_active = Column(Boolean, server_default="True", nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)

    role = Column(Enum("admin", "user", name="user_roles"), nullable=False, server_default="user")

    # Relationships
    carts = relationship("Cart", back_populates="user")
    addresses = relationship("Address", back_populates="user")
    #wishlist_items = relationship("Wishlist", back_populates="user")
    
    

    

class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
    total_amount = Column(Float, nullable=False)

    # Relationship with user
    user = relationship("User", back_populates="carts")

    # Relationship with cart items
    cart_items = relationship("CartItem", back_populates="cart")

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    cart_id = Column(Integer, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    variant_id = Column(Integer, ForeignKey("variants.id", ondelete="SET NULL"), nullable=True)  # ✅ Added variant_id
    quantity = Column(Integer, nullable=False)
    subtotal = Column(Float, nullable=False)

    # Relationships
    cart = relationship("Cart", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")
    variant = relationship("Variant")  # ✅ Added relationship to Variant


# Association table for many-to-many relationship
product_categories = Table(
    "product_categories",
    Base.metadata,
    Column("product_id", Integer, ForeignKey("products.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id"), primary_key=True),
)


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    image_url = Column(String, nullable=True)  # Store the image path
    # Relationship with products
    products = relationship("Product", secondary=product_categories, back_populates="categories")
    parent = relationship("Category", remote_side=[id], backref="children")

# Association table must be defined first
product_tags = Table(
    "product_tags",
    Base.metadata,
    Column("product_id", Integer, ForeignKey("products.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    products = relationship("Product", secondary=product_tags, back_populates="tags")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    discount_percentage = Column(Float, nullable=False)
    rating = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)
    brand = Column(String, nullable=False)
    thumbnail = Column(String, nullable=False)
    images = Column(JSON, nullable=False)
    is_published = Column(Boolean, server_default="True", nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)

    # Many-to-Many Relationship with Categories
    categories = relationship("Category", secondary=product_categories, back_populates="products")

    # Relationship with cart items
    cart_items = relationship("CartItem", back_populates="product")
    
    # Relationship with wishlist
    wishlist_items = relationship("WishlistItem", back_populates="product")
    
    # Relationship with orders
    order_items = relationship("OrderItem", back_populates="product")

    # variants = relationship("Variant", back_populates="product")
    product_metadata = relationship("ProductMetadata", back_populates="product", cascade="all, delete-orphan", lazy="joined")

    tags = relationship("Tag", secondary=product_tags, back_populates="products")

    projects = relationship("Project", back_populates="product")



class ProductMetadata(Base):
    __tablename__ = "product_metadata"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)  # ✅ Fixed table name
    meta_key = Column(String, nullable=False)  # ✅ Match Pydantic field
    meta_value = Column(LONGTEXT, nullable=False)  # ✅ Match Pydantic field

    product = relationship("Product", back_populates="product_metadata")

class Variant(Base):
    __tablename__ = "variants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    value = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    # product_id = Column(Integer, ForeignKey("products.id"))
    product_id = Column(Integer,nullable=True)
    # product = relationship("Product", back_populates="variants")

class OTPStore(Base):
    __tablename__ = "otp_store"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    otp = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False, default=datetime.utcnow() + timedelta(minutes=10))

class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    street = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    country = Column(String, nullable=False)
    postal_code = Column(String, nullable=False)
    address_type = Column(String, nullable=False)
    address_name = Column(String, nullable=True)

    user = relationship("User", back_populates="addresses")

class Wishlist(Base):
    __tablename__ = "wishlists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    # items = relationship("WishlistItem", back_populates="wishlist")
    # user = relationship("User", back_populates="wishlists")
    items = relationship("WishlistItem", back_populates="wishlist", lazy="joined")

class WishlistItem(Base):
    __tablename__ = "wishlist_items"

    id = Column(Integer, primary_key=True, index=True)
    wishlist_id = Column(Integer, ForeignKey("wishlists.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    variant_id = Column(Integer, ForeignKey("variants.id", ondelete="SET NULL"), nullable=True)  # ✅ Added variant_id

    wishlist = relationship("Wishlist", back_populates="items")
    product = relationship("Product", back_populates="wishlist_items", lazy="joined")
    variant = relationship("Variant")  # ✅ Added relationship to Variant

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_amount = Column(Float, nullable=False)
    payment_status = Column(String, default="pending", nullable=False)
    project_id = Column(Integer, nullable=False)
    gallery_id = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)

    order_items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    subtotal = Column(Float, nullable=False)

    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")

 
class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # Store user ID
    product_id = Column(Integer,  ForeignKey("products.id"),nullable=False)
    prompt_id = Column(Integer, ForeignKey("prompts.id"), nullable=True)
    user_parameters = Column(JSON, nullable=False)
    preview_image_urls = Column(JSON, nullable=True)
    display_on_ui = Column(Boolean, nullable=True)
    reference_image=Column(String, nullable=True)
    remix = Column(Boolean, nullable=True)
    is_deleted = Column(Boolean, default=False) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="projects")
    prompt = relationship("Prompt", back_populates="projects")

class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # Store user ID
    prompt = Column(JSON, nullable=False)
    image_urls = Column(JSON, default=[]) 
    magic_prompt = Column(JSON, nullable=False)
    user_parameters = Column(JSON, nullable=False)
    story_title = Column(JSON, nullable=False)
    story=Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    
    projects = relationship("Project", back_populates="prompt")


class ImageStyle(Base):
    __tablename__ = "image_styles"

    id = Column(Integer, primary_key=True, index=True)
    slno=Column(String, nullable=False)
    style_category=Column(String, nullable=False)
    style_name = Column(String, nullable=False)
    ui_parameters=Column(Text, nullable=True)
    url = Column(String, nullable=False)
    endpoint = Column(Text, nullable=True)
    ref_keywords=Column(Text, nullable=True)  # ✅ NEW FIELD
    is_ai = Column(Boolean, nullable=True)
    is_display = Column(Boolean, default=True)

class AppSettings(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)
    app_key = Column(String, unique=True, index=True)
    label = Column(String, unique=True)
    app_value = Column(String)

class Gallery(Base):
    __tablename__ = "gallery"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, index=True, nullable=False)
    image_url = Column(String, nullable=False)
    original_img_url = Column(String, nullable=False)

class Playground(Base):
    __tablename__ = "playground"

    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    provider = Column(String, nullable=False)
    aspect_ratio = Column(String, default="")
    output_format = Column(String, default="jpeg")
    image_url = Column(Text, nullable=True)      # For Ideogram/Remix
    seed = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())    

class GalleryKeyword(Base):
    __tablename__ = "gallery_keywords"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String, unique=True, nullable=False)
    is_display = Column(Boolean, default=True)
    is_suggest = Column(Boolean, default=False)


class Organization(Base):
    __tablename__ = "organizations"

    org_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    company_name = Column(String, nullable=True)
    org_type = Column(String, nullable=False)
    brn_no = Column(String, nullable=True)
    personal_id = Column(String, nullable=True)
    id_type = Column(String, nullable=True)
    status = Column(
        Enum("active", "inactive", "suspended", name="org_status"),
        default="active",
        nullable=False
    )
    # Address
    address1 = Column(String)
    address2 = Column(String)
    floor_no = Column(String)
    unit_no = Column(String)
    postal_code = Column(String)
    city = Column(String)
    district = Column(String)
    state = Column(String)
    country = Column(String)
    # Contact
    email = Column(String)
    phone = Column(String)
    # Geo
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)
    timezone = Column(String)
    map_url = Column(String)
    location_source = Column(String)
    accuracy_meters = Column(Float)
    parent_org_id = Column(Integer, ForeignKey("organizations.org_id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # Relationships
    parent = relationship("Organization", remote_side=[org_id], backref="children")
    users = relationship("OrgUser", back_populates="organization")

class OrgUser(Base):
    __tablename__ = "org_users"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey("organizations.org_id"), nullable=False)
    full_name = Column(String, nullable=False)
    user_role = Column(String, nullable=False)
    user_type = Column(String, nullable=False)
    personal_id = Column(String)
    id_type = Column(String)
    status = Column(
        Enum("active", "inactive", "blocked", name="org_user_status"),
        default="active",
        nullable=False
    )
    email_id = Column(String, nullable=False)
    phone = Column(String)
    address = Column(String)
    postal_code = Column(String)
    city = Column(String)
    state = Column(String)
    country = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization", back_populates="users")