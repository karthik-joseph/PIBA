"""
Management command: seed_pets
-------------------------------
Seeds the database with:
  - Pet categories (Dog, Cat, Bird, Fish, Rabbit, Hamster)
  - Breeds per category (realistic data)
  - 3 demo seller accounts + SellerProfile
  - 40+ pet listings with images sourced from static/images/pet_listing/
  - PetImage records using static file paths (copied to MEDIA_ROOT)

Usage:
    python manage.py seed_pets
    python manage.py seed_pets --clear   # wipe existing pets/categories/breeds first
"""

import os
import shutil
import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils.text import slugify
from django.core.files import File

from pets.models import PetCategory, Breed, Pet, PetImage
from sellers.models import SellerProfile

User = get_user_model()

# ─────────────────────────────────────────────
# Static image base directory
# ─────────────────────────────────────────────
STATIC_PETS_DIR = os.path.join(settings.BASE_DIR, 'static', 'images', 'pet_listing')


def _static_images(subdir):
    """Return list of absolute paths for all images in a static subdirectory."""
    folder = os.path.join(STATIC_PETS_DIR, subdir)
    if not os.path.isdir(folder):
        return []
    return [
        os.path.join(folder, f)
        for f in sorted(os.listdir(folder))
        if os.path.isfile(os.path.join(folder, f))
    ]


# ─────────────────────────────────────────────
# CATEGORIES
# ─────────────────────────────────────────────
CATEGORIES = [
    {'name': 'Dogs',    'slug': 'dogs',    'icon': 'dog.svg',    'description': 'Loyal and loving companions for every family.',     'display_order': 1},
    {'name': 'Cats',    'slug': 'cats',    'icon': 'cat.svg',    'description': 'Independent and affectionate feline friends.',       'display_order': 2},
    {'name': 'Birds',   'slug': 'birds',   'icon': 'bird.svg',   'description': 'Colourful and cheerful feathered companions.',      'display_order': 3},
    {'name': 'Fish',    'slug': 'fish',    'icon': 'fish.svg',   'description': 'Peaceful aquatic pets for any home.',               'display_order': 4},
    {'name': 'Rabbits', 'slug': 'rabbits', 'icon': 'rabbit.svg', 'description': 'Gentle and fluffy small pets, perfect indoors.',   'display_order': 5},
    {'name': 'Hamsters','slug': 'hamsters','icon': 'hamster.svg','description': 'Tiny, playful rodents great for small spaces.',    'display_order': 6},
]

# ─────────────────────────────────────────────
# BREEDS  { category_slug: [(name, size, lifespan, temperament)] }
# ─────────────────────────────────────────────
BREEDS = {
    'dogs': [
        ('Labrador Retriever', 'large',  '10–12 years', 'Friendly, outgoing, active'),
        ('Golden Retriever',   'large',  '10–12 years', 'Reliable, trustworthy, kind'),
        ('German Shepherd',    'large',  '9–13 years',  'Confident, courageous, smart'),
        ('Beagle',             'small',  '12–15 years', 'Merry, friendly, curious'),
        ('Poodle',             'medium', '12–15 years', 'Intelligent, active, alert'),
        ('Bulldog',            'medium', '8–10 years',  'Docile, willful, friendly'),
        ('Chihuahua',          'tiny',   '12–18 years', 'Charming, graceful, sassy'),
        ('Pomeranian',         'tiny',   '12–16 years', 'Inquisitive, bold, lively'),
        ('Rottweiler',         'large',  '8–10 years',  'Loyal, loving, confident'),
        ('Siberian Husky',     'large',  '12–14 years', 'Loyal, mischievous, outgoing'),
        ('Dachshund',          'small',  '12–16 years', 'Curious, friendly, spunky'),
        ('French Bulldog',     'small',  '10–12 years', 'Playful, adaptable, smart'),
        ('Yorkshire Terrier',  'tiny',   '11–15 years', 'Affectionate, spritely, tomboyish'),
        ('Dobermann',          'large',  '10–13 years', 'Alert, fearless, loyal'),
        ('Border Collie',      'medium', '12–15 years', 'Intelligent, energetic, alert'),
        ('Pug',                'small',  '12–15 years', 'Charming, mischievous, loving'),
        ('Australian Shepherd','medium', '13–15 years', 'Smart, work-oriented, energetic'),
        ('Maltese',            'tiny',   '12–15 years', 'Gentle, playful, fearless'),
        ('Boxer',              'large',  '10–12 years', 'Playful, devoted, energetic'),
        ('Airedale Terrier',   'large',  '11–14 years', 'Friendly, courageous, intelligent'),
    ],
    'cats': [
        ('Persian',              'medium', '12–17 years', 'Sweet, gentle, quiet'),
        ('Siamese',              'medium', '12–15 years', 'Social, vocal, active'),
        ('Maine Coon',           'large',  '12–15 years', 'Clever, gentle, playful'),
        ('Ragdoll',              'large',  '12–15 years', 'Gentle, calm, affectionate'),
        ('Bengal',               'medium', '12–16 years', 'Active, playful, intelligent'),
        ('British Shorthair',    'medium', '14–20 years', 'Calm, easy-going, loyal'),
        ('Abyssinian',           'medium', '9–15 years',  'Curious, playful, active'),
        ('Scottish Fold',        'medium', '11–15 years', 'Gentle, quiet, adaptable'),
        ('Russian Blue',         'medium', '15–20 years', 'Gentle, shy with strangers, loyal'),
        ('Birman',               'medium', '12–16 years', 'Affectionate, gentle, active'),
        ('American Shorthair',   'medium', '15–20 years', 'Easy-going, even-tempered'),
        ('Sphynx',               'medium', '8–14 years',  'Energetic, curious, friendly'),
        ('Turkish Angora',       'medium', '12–18 years', 'Playful, intelligent, active'),
        ('Bombay',               'medium', '12–16 years', 'Affectionate, curious, playful'),
        ('Munchkin',             'small',  '12–15 years', 'Sociable, curious, playful'),
    ],
    'birds': [
        ('African Grey Parrot',  'medium', '40–60 years', 'Intelligent, loyal, curious'),
        ('Budgerigar',           'tiny',   '5–10 years',  'Social, playful, affectionate'),
        ('Cockatiel',            'small',  '10–15 years', 'Gentle, friendly, curious'),
        ('Sun Conure',           'small',  '20–30 years', 'Energetic, cuddly, vocal'),
        ('Lovebird',             'tiny',   '10–15 years', 'Affectionate, social, playful'),
        ('Indian Ringneck',      'small',  '25–30 years', 'Intelligent, independent, vocal'),
        ('Macaw',                'large',  '50–60 years', 'Intelligent, social, colourful'),
        ('Finch',                'tiny',   '5–10 years',  'Active, social, low-maintenance'),
        ('Yellow Canary',        'tiny',   '10–15 years', 'Cheerful, musical, calm'),
        ('Pink Cockatoo',        'medium', '40–60 years', 'Affectionate, playful, intelligent'),
    ],
    'fish': [
        ('Goldfish',      'small',  '10–15 years', 'Peaceful, social'),
        ('Betta Fish',    'tiny',   '2–5 years',   'Bold, elegant'),
        ('Clownfish',     'tiny',   '6–10 years',  'Active, playful'),
        ('Guppy',         'tiny',   '1–3 years',   'Hardy, colourful, social'),
        ('Blue Tang',     'medium', '8–20 years',  'Lively, sociable'),
        ('Yellow Tang',   'medium', '5–10 years',  'Energetic, bold'),
        ('Tetra',         'tiny',   '5–10 years',  'Peaceful, schooling'),
        ('Green Chromis', 'tiny',   '5–8 years',   'Peaceful, hardy'),
    ],
    'rabbits': [
        ('Mini Lop',       'small',  '7–14 years', 'Playful, gentle, curious'),
        ('Harlequin',      'medium', '5–8 years',  'Playful, curious, gentle'),
        ('Rex',            'medium', '5–6 years',  'Intelligent, affectionate, calm'),
        ('Angora',         'medium', '5–8 years',  'Gentle, calm, sociable'),
    ],
    'hamsters': [
        ('Syrian Hamster',      'tiny', '2–3 years', 'Solitary, docile, curious'),
        ('Dwarf Hamster',       'tiny', '1–3 years', 'Social, active, fast'),
        ('Roborovski Hamster',  'tiny', '3–4 years', 'Shy, energetic, small'),
    ],
}

# ─────────────────────────────────────────────
# SELLER ACCOUNTS
# ─────────────────────────────────────────────
SELLERS_DATA = [
    {
        'email': 'pawspalace@piba.com',
        'username': 'pawspalace',
        'first_name': 'Rajesh',
        'last_name': 'Kumar',
        'password': 'seller@123',
        'role': 'seller',
        'business_name': "Paws Palace",
        'business_type': 'kennel',
        'phone': '9876543210',
        'address': '12, MG Road',
        'city': 'Bengaluru',
        'state': 'Karnataka',
        'postal_code': '560001',
        'description': 'Premium kennel and breeder with 15 years of experience. All pets are vaccinated and health-checked.',
        'is_verified': True,
    },
    {
        'email': 'petparadise@piba.com',
        'username': 'petparadise',
        'first_name': 'Priya',
        'last_name': 'Sharma',
        'password': 'seller@123',
        'role': 'seller',
        'business_name': "Pet Paradise",
        'business_type': 'pet_shop',
        'phone': '9123456789',
        'address': '45, Anna Salai',
        'city': 'Chennai',
        'state': 'Tamil Nadu',
        'postal_code': '600002',
        'description': 'Your one-stop pet paradise — dogs, cats, birds, and more, all ethically sourced.',
        'is_verified': True,
    },
    {
        'email': 'happypaws_shelter@piba.com',
        'username': 'happypaws',
        'first_name': 'Anita',
        'last_name': 'Nair',
        'password': 'seller@123',
        'role': 'seller',
        'business_name': "Happy Paws Shelter",
        'business_type': 'shelter',
        'phone': '9001234567',
        'address': '78, Bandra West',
        'city': 'Mumbai',
        'state': 'Maharashtra',
        'postal_code': '400050',
        'description': 'A loving rescue shelter giving second chances to beautiful animals. Adoption-focused.',
        'is_verified': True,
    },
]

# ─────────────────────────────────────────────
# PET SEED DATA  (name, image_subdir, image_filename, breed_name, gender, age_y, age_m,
#                 color, weight, price, listing_type, health, vaccinated, neutered, featured, description)
# ─────────────────────────────────────────────
PETS_DATA = [
    # DOGS ──────────────────────────────────────
    ('Bruno', 'dog', 'golden-retriver.jpg', 'Golden Retriever', 'male', 1, 6, 'Golden', 22.0, 25000, 'sale', 'excellent', True, False, True,
     'Bruno is a cheerful and energetic Golden Retriever who loves outdoor adventures and cuddles. He is fully vaccinated, house-trained, and gets along perfectly with children and other pets.'),
    ('Luna', 'dog', 'labrador-retriver.webp', 'Labrador Retriever', 'female', 0, 8, 'Black', 14.0, 20000, 'sale', 'excellent', True, True, True,
     'Luna is a playful and gentle Labrador Retriever pup. She is very sociable, loves water, and is already learning her first commands. Perfect for active families.'),
    ('Max', 'dog', 'German-Shepherd-dog-Alsatian.webp', 'German Shepherd', 'male', 2, 0, 'Black and Tan', 30.0, 35000, 'sale', 'excellent', True, False, True,
     'Max is a trained German Shepherd with excellent guarding instincts. He responds to basic commands and is loyal, protective, and loving with his family.'),
    ('Bella', 'dog', 'pomeranian.webp', 'Pomeranian', 'female', 0, 5, 'Cream', 2.5, 18000, 'sale', 'good', True, False, False,
     'Bella is an adorable Pomeranian puppy with a fluffy double coat. She is lively, curious, and loves being the centre of attention. Ideal for apartment living.'),
    ('Rocky', 'dog', 'Rottweiler-dog.webp', 'Rottweiler', 'male', 1, 3, 'Black and Mahogany', 35.0, 30000, 'sale', 'excellent', True, False, True,
     'Rocky is a confident and well-socialized Rottweiler. He has been raised with children and is protective yet gentle with his family. A true gentle giant.'),
    ('Daisy', 'dog', 'Beagle_image.webp', 'Beagle', 'female', 0, 7, 'Tri-colour', 8.0, 15000, 'sale', 'good', True, False, False,
     'Daisy is a merry little Beagle with an irresistible nose. She loves sniffing adventures in the park and is great with kids and other dogs.'),
    ('Coco', 'dog', 'Chihuahua-dog.webp', 'Chihuahua', 'female', 1, 0, 'Fawn', 1.8, 12000, 'sale', 'good', True, True, False,
     'Coco is a feisty and loyal Chihuahua who thinks she is much bigger than she is! She is perfect for apartment living and loves snuggling under blankets.'),
    ('Duke', 'dog', 'Siberian-Husky-standing-outdoors-in-the-winter.avif', 'Siberian Husky', 'male', 1, 2, 'Black and White', 27.0, 40000, 'sale', 'excellent', True, False, True,
     'Duke is a striking Siberian Husky with piercing blue eyes. He is adventurous, playful, and loves cold weather. Needs daily exercise and a committed owner.'),
    ('Milo', 'dog', 'French-Bulldog-standing-outdoors.avif', 'French Bulldog', 'male', 0, 9, 'Brindle', 9.0, 45000, 'sale', 'good', True, False, True,
     'Milo is a bat-eared French Bulldog with loads of personality packed into a small body. He is adaptable, low-energy, and perfect for city life.'),
    ('Maggie', 'dog', 'border-collie-breed-dog.jpg', 'Border Collie', 'female', 2, 0, 'Black and White', 18.0, 22000, 'sale', 'excellent', True, True, False,
     'Maggie is an incredibly intelligent Border Collie who thrives on mental stimulation. She knows 20+ commands and loves agility training. She needs an experienced owner.'),
    ('Buddy', 'dog', 'golden-retriver-in-garden.jpg', 'Golden Retriever', 'male', 0, 6, 'Golden', 12.0, 22000, 'sale', 'good', True, False, False,
     'Buddy is a sweet Golden Retriever puppy who loves everyone he meets. He is growing fast and will be a wonderful family companion for years to come.'),
    ('Pepper', 'dog', 'Dachshund.webp', 'Dachshund', 'male', 1, 4, 'Chocolate', 7.5, 16000, 'sale', 'good', True, False, False,
     'Pepper is a curious and mischievous Dachshund who can follow a scent anywhere. He is stubborn but very lovable and keeps everyone entertained.'),

    # CATS ──────────────────────────────────────
    ('Whiskers', 'cat', 'spruce-pets-persian-cat.jpg', 'Persian', 'female', 2, 0, 'White', 4.5, 20000, 'sale', 'excellent', True, True, True,
     'Whiskers is a regal Persian with a luxurious white coat. She is calm, quiet, and loves being groomed and pampered. Perfect for a serene home environment.'),
    ('Simba', 'cat', 'Siamese-cat-beautiful.webp', 'Siamese', 'male', 1, 3, 'Seal Point', 5.0, 18000, 'sale', 'excellent', True, False, True,
     'Simba is a talkative and social Siamese who will follow you from room to room. He is incredibly intelligent and thrives on interaction and play.'),
    ('Mittens', 'cat', 'maine_coon_cat.jpg', 'Maine Coon', 'female', 1, 8, 'Brown Tabby', 7.0, 25000, 'sale', 'excellent', True, True, True,
     'Mittens is a majestic Maine Coon with tufted ears and a magnificent plumed tail. She is dog-like in her loyalty and loves to play fetch.'),
    ('Shadow', 'cat', 'bombay_cat.webp', 'Bombay', 'male', 0, 10, 'Jet Black', 3.5, 15000, 'sale', 'good', True, False, False,
     'Shadow is a sleek and glossy Bombay with copper-penny eyes. He is curious and playful, often described as a miniature panther who loves cuddles.'),
    ('Lily', 'cat', 'ragdoll.avif', 'Ragdoll', 'female', 1, 0, 'Blue Colourpoint', 6.5, 30000, 'sale', 'excellent', True, True, True,
     'Lily is a floppy, easy-going Ragdoll who goes limp when picked up. She is placid, affectionate, and absolutely perfect for families with children.'),
    ('Oliver', 'cat', 'british_shorthair.webp', 'British Shorthair', 'male', 2, 0, 'Blue', 6.0, 22000, 'sale', 'excellent', True, False, False,
     'Oliver is a plush British Shorthair with the most gorgeous blue-grey coat. He is independent but affectionate on his own terms — a true British gentleman.'),
    ('Cleo', 'cat', 'abyssinian.jpg', 'Abyssinian', 'female', 1, 5, 'Ruddy', 4.0, 16000, 'sale', 'good', True, False, False,
     'Cleo is an active and curious Abyssinian who is always on the move. She loves to climb, explore, and play. She will keep you entertained all day.'),
    ('Nala', 'cat', 'russian-blue-cats-1024x682.webp', 'Russian Blue', 'female', 2, 0, 'Blue-Grey', 5.0, 24000, 'sale', 'excellent', True, True, False,
     'Nala is a gentle and loyal Russian Blue who bonds deeply with one person. She is shy at first but incredibly affectionate once she trusts you.'),

    # ADOPTION cats ─────────────────────────────
    ('Patches', 'cat', 'scottish_fold_cat.webp', 'Scottish Fold', 'female', 3, 0, 'Calico', 4.5, 500, 'adoption', 'good', True, True, False,
     'Patches is a sweet 3-year-old rescue who has been through a lot but has so much love to give. She is gentle, house-trained, and ready for her forever home.'),
    ('Tom', 'cat', 'american_shorthair.jpg', 'American Shorthair', 'male', 4, 0, 'Silver Tabby', 5.5, 500, 'adoption', 'good', True, True, False,
     'Tom is a classic tabby with a laid-back personality. He is great with other cats and children, and he just needs a warm home to call his own.'),

    # BIRDS ─────────────────────────────────────
    ('Rio', 'bird', 'african_grey_web-1024x683.jpg', 'African Grey Parrot', 'male', 3, 0, 'Grey with Red Tail', 0.5, 80000, 'sale', 'excellent', True, False, True,
     'Rio is a remarkable African Grey with an impressive vocabulary of 150+ words. He loves music, puzzles, and learning new tricks. A truly extraordinary companion.'),
    ('Tweety', 'bird', 'budgerigars-perching-on-branch.jpg', 'Budgerigar', 'female', 0, 8, 'Sky Blue', 0.03, 2500, 'sale', 'good', True, False, False,
     'Tweety is a cheerful budgie who loves to chirp and chatter all day. She is easy to tame and will quickly learn to sit on your finger.'),
    ('Peaches', 'bird', 'cocktiel_birds.webp', 'Cockatiel', 'female', 1, 0, 'Lutino', 0.1, 5000, 'sale', 'good', True, False, False,
     'Peaches is a gentle cockatiel who can whistle tunes and loves gentle head scratches. She is perfect for first-time bird owners.'),
    ('Kiwi', 'bird', 'conures_sun_green_ckeeked.jpg', 'Sun Conure', 'male', 2, 0, 'Orange and Yellow', 0.12, 35000, 'sale', 'excellent', True, False, True,
     'Kiwi is a brilliantly coloured Sun Conure who is bold, cuddly, and loves being the star of every room. He will form an intense bond with his owner.'),
    ('Sunny', 'bird', 'yellow_canary.jpg', 'Yellow Canary', 'male', 1, 0, 'Yellow', 0.02, 3000, 'sale', 'good', False, False, False,
     'Sunny fills the room with beautiful singing every morning. He is low-maintenance and perfect for someone who appreciates birdsong without the fuss.'),
    ('Polly', 'bird', 'indian_ringneck_parrot.jpg', 'Indian Ringneck', 'female', 1, 6, 'Green', 0.15, 25000, 'sale', 'good', True, False, False,
     'Polly is a sharp and independent Indian Ringneck who is learning to talk. She is stunning in flight and loves foraging for treats.'),

    # FISH ──────────────────────────────────────
    ('Goldie', 'fish', 'Gold_fish1.jpg', 'Goldfish', 'unknown', 0, 6, 'Orange', 0.1, 500, 'sale', 'good', False, False, False,
     'Goldie is a lively common goldfish, brightest in the room. She comes with starter care instructions and thrives in a basic tank setup.'),
    ('Neptune', 'fish', 'betta_fish.webp', 'Betta Fish', 'male', 0, 4, 'Deep Blue', 0.005, 800, 'sale', 'excellent', False, False, True,
     'Neptune is a stunning Betta fish with flowing fins that shimmer like a jewel. Keep him solo in a well-planted tank for best results.'),
    ('Nemo', 'fish', 'clownfish.webp', 'Clownfish', 'unknown', 0, 8, 'Orange and White', 0.02, 1500, 'sale', 'good', False, False, True,
     'Just like the movie, Nemo is adventurous and striking. He does well with anemones in a saltwater reef setup. A real crowd-pleaser.'),
    ('Coral', 'fish', 'guppies_fish.webp', 'Guppy', 'female', 0, 3, 'Multicolour', 0.003, 200, 'sale', 'good', False, False, False,
     'Coral is a hardy and colourful guppy, ideal for community tanks. She is one of the best beginner fish. Available as a pair or trio.'),
    ('Dory', 'fish', 'blue_tang.webp', 'Blue Tang', 'unknown', 0, 10, 'Royal Blue', 0.08, 3500, 'sale', 'excellent', False, False, True,
     'Dory is a striking Blue Tang who commands attention in any saltwater aquarium. She needs space to swim and a well-established reef tank.'),
    ('Zigzag', 'fish', 'tetras.webp', 'Tetra', 'unknown', 0, 5, 'Neon Blue-Red', 0.002, 150, 'sale', 'good', False, False, False,
     'Zigzag and his school of Neon Tetras are sold as a group of 10. They create a dazzling display in any planted freshwater aquarium.'),

    # RABBITS ───────────────────────────────────
    ('Hopscotch', 'rabbit', 'mini_lop_rabbit.jpg', 'Mini Lop', 'female', 0, 5, 'Orange and White', 1.8, 6000, 'sale', 'good', True, False, True,
     'Hopscotch is an adorable Mini Lop with floppy ears and a round, cuddly body. She loves hopping around and exploring. Indoor litter-trained.'),
    ('Snowball', 'rabbit', 'white-angora-rabbit-on-grass.webp', 'Angora', 'male', 0, 8, 'Pure White', 2.5, 8000, 'sale', 'excellent', True, False, False,
     'Snowball is a fluffy Angora who looks like a cloud. His wool coat needs regular grooming, but the result is absolutely stunning. Very calm temperament.'),
    ('Thumper', 'rabbit', 'harlequin_rabbit.jpg', 'Harlequin', 'male', 1, 0, 'Black and Orange', 2.2, 5000, 'sale', 'good', True, False, False,
     'Thumper is a playful Harlequin rabbit with a distinctive patchwork coat. He is curious, active, and loves chin rubs. Great for older children.'),

    # ADOPTION rabbit ───────────────────────────
    ('Cottonbud', 'rabbit', 'harlequin_brown_black.webp', 'Rex', 'female', 2, 0, 'Brown and Black', 2.0, 300, 'adoption', 'good', True, True, False,
     'Cottonbud is a beautiful Rex rabbit who was surrendered by her previous owner. She is spayed, vaccinated, and very friendly. Looking for a forever home.'),
]


class Command(BaseCommand):
    help = 'Seed the database with realistic category, breed, seller, and pet data using static images.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing pets, breeds, and categories before seeding.'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data…'))
            PetImage.objects.all().delete()
            Pet.objects.all().delete()
            Breed.objects.all().delete()
            PetCategory.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('  → Cleared.'))

        # ── 1. Categories ────────────────────────────────
        self.stdout.write('\n📂 Creating categories…')
        cat_map = {}
        for c in CATEGORIES:
            obj, created = PetCategory.objects.get_or_create(
                slug=c['slug'],
                defaults={
                    'name': c['name'],
                    'icon': c['icon'],
                    'description': c['description'],
                    'display_order': c['display_order'],
                    'is_active': True,
                }
            )
            cat_map[c['slug']] = obj
            self.stdout.write(f"  {'✓ Created' if created else '· Exists ':} {obj.name}")

        # ── 2. Breeds ────────────────────────────────────
        self.stdout.write('\n🐾 Creating breeds…')
        breed_map = {}   # breed_name → Breed obj
        for cat_slug, breed_list in BREEDS.items():
            cat_obj = cat_map.get(cat_slug)
            if not cat_obj:
                continue
            for (name, size, lifespan, temperament) in breed_list:
                obj, created = Breed.objects.get_or_create(
                    category=cat_obj,
                    name=name,
                    defaults={
                        'average_size': size,
                        'average_lifespan': lifespan,
                        'temperament': temperament,
                        'is_active': True,
                    }
                )
                breed_map[name] = obj
                self.stdout.write(f"  {'✓':} {cat_obj.name} → {name}")

        # ── 3. Sellers ───────────────────────────────────
        self.stdout.write('\n🏪 Creating demo sellers…')
        seller_objs = []
        for sd in SELLERS_DATA:
            user, u_created = User.objects.get_or_create(
                email=sd['email'],
                defaults={
                    'username': sd['username'],
                    'first_name': sd['first_name'],
                    'last_name': sd['last_name'],
                    'role': sd['role'],
                    'is_active': True,
                }
            )
            if u_created:
                user.set_password(sd['password'])
                user.save()
                self.stdout.write(f"  ✓ User created: {user.email}")
            else:
                self.stdout.write(f"  · User exists: {user.email}")

            sp, sp_created = SellerProfile.objects.get_or_create(
                user=user,
                defaults={
                    'business_name': sd['business_name'],
                    'business_type': sd['business_type'],
                    'phone': sd['phone'],
                    'address': sd['address'],
                    'city': sd['city'],
                    'state': sd['state'],
                    'postal_code': sd['postal_code'],
                    'country': 'India',
                    'description': sd['description'],
                    'is_verified': sd['is_verified'],
                    'is_active': True,
                }
            )
            if sp_created:
                self.stdout.write(f"    ✓ SellerProfile created: {sp.business_name}")
            seller_objs.append(sp)

        # ── 4. Pets ──────────────────────────────────────
        self.stdout.write('\n🐶 Creating pet listings…')
        media_pets_dir = os.path.join(settings.MEDIA_ROOT, 'pet_images')
        os.makedirs(media_pets_dir, exist_ok=True)

        # Map category by slug abbreviation used in PETS_DATA
        cat_alias = {
            'dog':    cat_map.get('dogs'),
            'cat':    cat_map.get('cats'),
            'bird':   cat_map.get('birds'),
            'fish':   cat_map.get('fish'),
            'rabbit': cat_map.get('rabbits'),
        }

        seller_cycle = 0
        for pet_data in PETS_DATA:
            (
                name, img_subdir, img_file, breed_name,
                gender, age_y, age_m, color, weight,
                price, listing_type, health,
                vaccinated, neutered, featured, description
            ) = pet_data

            category = cat_alias.get(img_subdir)
            if not category:
                self.stdout.write(self.style.WARNING(f'  ⚠ Unknown subdir {img_subdir}, skipping {name}'))
                continue

            breed = breed_map.get(breed_name)
            seller = seller_objs[seller_cycle % len(seller_objs)]
            seller_cycle += 1

            # Skip if a pet with this name+breed already exists
            if Pet.objects.filter(name=name, breed=breed).exists():
                self.stdout.write(f'  · Exists: {name}')
                continue

            pet = Pet.objects.create(
                name=name,
                category=category,
                breed=breed,
                seller=seller,
                gender=gender,
                age_years=age_y,
                age_months=age_m,
                color=color,
                weight=weight,
                price=price,
                listing_type=listing_type,
                status='available',
                health_status=health,
                is_vaccinated=vaccinated,
                is_neutered=neutered,
                is_featured=featured,
                is_approved=True,
                is_active=True,
                description=description,
            )

            # Attach image
            src_path = os.path.join(STATIC_PETS_DIR, img_subdir, img_file)
            if os.path.isfile(src_path):
                dst_name = f"pet_{pet.pk}_{img_file}"
                dst_path = os.path.join(media_pets_dir, dst_name)
                shutil.copy2(src_path, dst_path)
                with open(dst_path, 'rb') as f:
                    pet_image = PetImage(pet=pet, is_primary=True, display_order=0)
                    pet_image.image.save(dst_name, File(f), save=True)
                self.stdout.write(f'  ✓ {name} [{category.name}] → image attached')
            else:
                self.stdout.write(self.style.WARNING(f'  ⚠ {name}: image not found at {src_path}'))

        total = Pet.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'\n🎉 Done! {total} total pets in database.\n'
            f'   Categories: {PetCategory.objects.count()}\n'
            f'   Breeds:     {Breed.objects.count()}\n'
            f'   Sellers:    {SellerProfile.objects.count()}\n'
        ))
