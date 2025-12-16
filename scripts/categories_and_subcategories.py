"""Seed script to insert categories and subcategories into the database."""
import asyncio
import sys
import traceback
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, func
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from src.config import settings
from src.taxonomy.models import Category, Subcategory

# Ensure models are registered so relationships resolve
import src.users.models  # noqa: F401


async def check_tables_exist(session: AsyncSession) -> bool:
    """Check if database tables exist."""
    try:
        await session.execute(select(func.count()).select_from(Category))
        return True
    except ProgrammingError as e:
        error_str = str(e).lower()
        if "does not exist" in error_str or "relation" in error_str:
            return False
        raise


# Categories data from database_tables.md
CATEGORIES_DATA = [
    {"name": "Identity", "description": "Personal identification documents"},
    {"name": "Educational", "description": "Academic certificates and records"},
    {"name": "Professional", "description": "Employment and career documents"},
    {"name": "Financial", "description": "Banking, tax, and investment documents"},
    {"name": "Insurance", "description": "Insurance policies and claims"},
    {"name": "Bills & Receipts", "description": "Utility bills and purchase receipts"},
    {"name": "Contracts", "description": "Legal agreements and contracts"},
    {"name": "Property", "description": "Real estate and property documents"},
    {"name": "Vehicle", "description": "Vehicle registration and related docs"},
    {"name": "Medical", "description": "Health records and prescriptions"},
    {"name": "Legal", "description": "Court orders and legal documents"},
    {"name": "Travel", "description": "Visa and travel related documents"},
    {"name": "Warranty", "description": "Product warranties and AMC documents"},
    {"name": "Membership", "description": "Club and subscription memberships"},
    {"name": "Others", "description": "Miscellaneous documents"},
]

# Subcategories data from database_tables.md
# Format: (category_name, name, description)
SUBCATEGORIES_DATA = [
    # Identity (CAT001)
    ("Identity", "Aadhar Card", "12-digit unique identification"),
    ("Identity", "PAN Card", "Permanent Account Number for tax"),
    ("Identity", "Voter ID", "Election identity card"),
    ("Identity", "Passport", "International travel document"),
    ("Identity", "Driving License", "Vehicle driving permit"),
    ("Identity", "Birth Certificate", "Proof of birth"),
    ("Identity", "Marriage Certificate", "Proof of marriage"),
    ("Identity", "Ration Card", "Food subsidy entitlement"),
    # Educational (CAT002)
    ("Educational", "Degree Certificate", "University degree"),
    ("Educational", "Marksheet", "Academic score records"),
    ("Educational", "Transcript", "Detailed academic records"),
    ("Educational", "Migration Certificate", "Transfer between institutions"),
    ("Educational", "Diploma Certificate", "Professional diploma"),
    ("Educational", "Course Certificate", "Short course completion"),
    # Professional (CAT003)
    ("Professional", "Resume/CV", "Career summary document"),
    ("Professional", "Offer Letter", "Job offer documentation"),
    ("Professional", "Experience Letter", "Work experience proof"),
    ("Professional", "Payslip", "Monthly salary statement"),
    ("Professional", "Relieving Letter", "Employment termination proof"),
    ("Professional", "Appraisal Letter", "Performance review document"),
    # Financial (CAT004)
    ("Financial", "Bank Statement", "Account transaction records"),
    ("Financial", "Tax Returns", "Income tax filing documents"),
    ("Financial", "Investment Document", "Mutual funds, stocks, bonds"),
    ("Financial", "FD Receipt", "Fixed deposit certificate"),
    ("Financial", "Loan Document", "Loan agreement and EMI details"),
    ("Financial", "Credit Card Statement", "Monthly credit card records"),
    # Insurance (CAT005)
    ("Insurance", "Life Insurance", "Life coverage policy"),
    ("Insurance", "Health Insurance", "Medical coverage policy"),
    ("Insurance", "Vehicle Insurance", "Car/bike insurance policy"),
    ("Insurance", "Home Insurance", "Property insurance policy"),
    ("Insurance", "Travel Insurance", "Trip coverage policy"),
    ("Insurance", "Insurance Claim", "Claim submission documents"),
    # Bills & Receipts (CAT006)
    ("Bills & Receipts", "Electricity Bill", "Power utility bill"),
    ("Bills & Receipts", "Water Bill", "Water utility bill"),
    ("Bills & Receipts", "Gas Bill", "Gas utility bill"),
    ("Bills & Receipts", "Internet Bill", "Broadband/WiFi bill"),
    ("Bills & Receipts", "Mobile Bill", "Phone bill"),
    ("Bills & Receipts", "Purchase Receipt", "Product purchase proof"),
    ("Bills & Receipts", "Invoice", "Service/product invoice"),
    # Contracts (CAT007)
    ("Contracts", "Rental Agreement", "House/office rent contract"),
    ("Contracts", "Employment Contract", "Job terms and conditions"),
    ("Contracts", "NDA", "Non-disclosure agreement"),
    ("Contracts", "Sale Deed", "Property sale agreement"),
    ("Contracts", "Service Agreement", "Service provider contract"),
    # Property (CAT008)
    ("Property", "Property Registration", "Registered property deed"),
    ("Property", "Land Records", "Land ownership documents"),
    ("Property", "House Tax Receipt", "Property tax payment"),
    ("Property", "Society Documents", "Housing society papers"),
    ("Property", "Encumbrance Certificate", "Property liability proof"),
    # Vehicle (CAT009)
    ("Vehicle", "RC Book", "Vehicle registration certificate"),
    ("Vehicle", "PUC Certificate", "Pollution under control certificate"),
    ("Vehicle", "Vehicle Service Record", "Maintenance history"),
    ("Vehicle", "Challan Receipt", "Traffic fine payment"),
    # Medical (CAT010)
    ("Medical", "Health Report", "Medical checkup results"),
    ("Medical", "Prescription", "Doctor's medication order"),
    ("Medical", "Lab Report", "Diagnostic test results"),
    ("Medical", "Vaccination Record", "Immunization history"),
    ("Medical", "Discharge Summary", "Hospital discharge papers"),
    ("Medical", "Medical Bill", "Hospital/clinic payment"),
    # Legal (CAT011)
    ("Legal", "Court Order", "Judicial order document"),
    ("Legal", "Affidavit", "Sworn statement"),
    ("Legal", "FIR Copy", "Police complaint copy"),
    ("Legal", "Power of Attorney", "Legal authority delegation"),
    ("Legal", "Will", "Testament document"),
    ("Legal", "Succession Certificate", "Inheritance proof"),
    # Travel (CAT012)
    ("Travel", "Visa Document", "Travel visa"),
    ("Travel", "Boarding Pass", "Flight boarding ticket"),
    ("Travel", "Hotel Booking", "Accommodation confirmation"),
    ("Travel", "Itinerary", "Travel plan details"),
    ("Travel", "Travel Ticket", "Train/bus/flight ticket"),
    # Warranty (CAT013)
    ("Warranty", "Product Warranty", "Manufacturer warranty card"),
    ("Warranty", "Extended Warranty", "Additional warranty coverage"),
    ("Warranty", "AMC Document", "Annual maintenance contract"),
    # Membership (CAT014)
    ("Membership", "Gym Membership", "Fitness club membership"),
    ("Membership", "Club Membership", "Social/sports club membership"),
    ("Membership", "Library Card", "Library membership"),
    ("Membership", "Subscription", "Digital/service subscription"),
    # Others (CAT015)
    ("Others", "Other Document", "Miscellaneous document"),
]


async def seed_categories_and_subcategories() -> None:
    """Seed categories and subcategories into the database."""
    print("=" * 60)
    print("Categories and Subcategories Seeding Script")
    print("=" * 60)
    print(f"\nDatabase URL: {settings.database_url.split('@')[0]}@***")  # Hide password
    print(f"Environment: {settings.environment}")

    # Create async engine using project settings
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=3600,
    )

    # Create async session maker
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        async with async_session() as session:
            # Check if tables exist
            print("\nChecking if database tables exist...")
            if not await check_tables_exist(session):
                print("⚠️  Database tables don't exist yet. Please run migrations first:")
                print("   alembic upgrade head")
                print("\n   Then run this script again:")
                print("   docker compose exec api python scripts/categories_and_subcategories.py")
                print("\n   Or locally:")
                print("   python scripts/categories_and_subcategories.py")
                return

            # Step 1: Create/Update Categories
            print("\nCreating/updating categories...")
            category_map = {}  # Map category name to Category object
            created_categories = []

            for category_data in CATEGORIES_DATA:
                try:
                    # Check if category already exists
                    result = await session.execute(
                        select(Category).where(
                            Category.name == category_data["name"], Category.is_del == False
                        )
                    )
                    existing_category = result.scalar_one_or_none()

                    if existing_category:
                        # Update existing category if description changed
                        updated = False
                        if existing_category.description != category_data["description"]:
                            existing_category.description = category_data["description"]
                            updated = True

                        if updated:
                            await session.flush()
                            print(f"  ✅ Updated category: {category_data['name']}")
                        else:
                            print(f"  ✅ Category already exists: {category_data['name']}")
                        category_map[category_data["name"]] = existing_category
                        created_categories.append(existing_category)
                    else:
                        # Create new category
                        new_category = Category(
                            name=category_data["name"],
                            description=category_data["description"],
                            created_by=None,
                            updated_by=None,
                        )
                        session.add(new_category)
                        await session.flush()
                        print(f"  ✅ Created category: {category_data['name']}")
                        category_map[category_data["name"]] = new_category
                        created_categories.append(new_category)

                except Exception as e:
                    await session.rollback()
                    print(f"  ❌ Error creating category {category_data['name']}: {e}")
                    raise

            # Commit categories first (subcategories depend on them)
            await session.commit()
            print(f"\n✅ Created/Updated {len(created_categories)} categories")

            # Step 2: Create/Update Subcategories
            print("\nCreating/updating subcategories...")
            created_subcategories = []

            for category_name, subcategory_name, subcategory_description in SUBCATEGORIES_DATA:
                try:
                    # Get the category object
                    category = category_map.get(category_name)
                    if not category:
                        print(f"  ⚠️  Warning: Category '{category_name}' not found, skipping subcategory '{subcategory_name}'")
                        continue

                    # Check if subcategory already exists
                    result = await session.execute(
                        select(Subcategory).where(
                            Subcategory.category_id == category.id,
                            Subcategory.name == subcategory_name,
                            Subcategory.is_del == False
                        )
                    )
                    existing_subcategory = result.scalar_one_or_none()

                    if existing_subcategory:
                        # Update existing subcategory if description changed
                        updated = False
                        if existing_subcategory.description != subcategory_description:
                            existing_subcategory.description = subcategory_description
                            updated = True

                        if updated:
                            await session.flush()
                            print(f"  ✅ Updated subcategory: {subcategory_name} (in {category_name})")
                        else:
                            print(f"  ✅ Subcategory already exists: {subcategory_name} (in {category_name})")
                        created_subcategories.append(existing_subcategory)
                    else:
                        # Create new subcategory
                        new_subcategory = Subcategory(
                            category_id=category.id,
                            name=subcategory_name,
                            description=subcategory_description,
                            created_by=None,
                            updated_by=None,
                        )
                        session.add(new_subcategory)
                        await session.flush()
                        print(f"  ✅ Created subcategory: {subcategory_name} (in {category_name})")
                        created_subcategories.append(new_subcategory)

                except Exception as e:
                    await session.rollback()
                    print(f"  ❌ Error creating subcategory {subcategory_name} in {category_name}: {e}")
                    raise

            # Commit all subcategories
            await session.commit()

            print("\n" + "=" * 60)
            print("✅ Categories and Subcategories created/updated successfully!")
            print("=" * 60)
            print(f"\nCreated/Updated Categories: {len(created_categories)}")
            for category in created_categories:
                subcats_count = len([s for s in created_subcategories if s.category_id == category.id])
                print(f"  - {category.name} (id: {category.id}) - {subcats_count} subcategories")
            print(f"\nCreated/Updated Subcategories: {len(created_subcategories)}")
            print("\n" + "=" * 60)

    except Exception as e:
        print(f"\n❌ Error seeding categories and subcategories: {e}")
        print(f"Error type: {type(e).__name__}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


async def main() -> None:
    """Main function to run the seeding script."""
    await seed_categories_and_subcategories()


if __name__ == "__main__":
    asyncio.run(main())

