from django.core.management.base import BaseCommand
from admission.models import Room, Bed


class Command(BaseCommand):
    help = 'Setup sample rooms and beds for the admission system'

    def handle(self, *args, **kwargs):
        self.stdout.write('Setting up rooms and beds...\n')

        # Clear existing data
        Bed.objects.all().delete()
        Room.objects.all().delete()

        # Create General Ward Rooms
        rooms_data = [
            {
                'room_number': 'R101',
                'room_type': 'general',
                'floor': 'Ground Floor',
                'daily_rate': 2000,
                'beds': ['B1', 'B2', 'B3']
            },
            {
                'room_number': 'R102',
                'room_type': 'general',
                'floor': 'Ground Floor',
                'daily_rate': 2000,
                'beds': ['B1', 'B2', 'B3']
            },
            {
                'room_number': 'R103',
                'room_type': 'general',
                'floor': 'Ground Floor',
                'daily_rate': 2000,
                'beds': ['B1', 'B2']
            },
            # Private Rooms
            {
                'room_number': 'R201',
                'room_type': 'private',
                'floor': 'First Floor',
                'daily_rate': 5000,
                'beds': ['B1', 'B2']
            },
            {
                'room_number': 'R202',
                'room_type': 'private',
                'floor': 'First Floor',
                'daily_rate': 5000,
                'beds': ['B1', 'B2']
            },
            # ICU
            {
                'room_number': 'ICU-1',
                'room_type': 'icu',
                'floor': 'First Floor',
                'daily_rate': 10000,
                'beds': ['B1', 'B2', 'B3']
            },
            {
                'room_number': 'ICU-2',
                'room_type': 'icu',
                'floor': 'First Floor',
                'daily_rate': 10000,
                'beds': ['B1', 'B2']
            },
            # Emergency
            {
                'room_number': 'ER-1',
                'room_type': 'emergency',
                'floor': 'Ground Floor',
                'daily_rate': 7500,
                'beds': ['B1', 'B2', 'B3', 'B4']
            },
        ]

        total_rooms = 0
        total_beds = 0

        for room_data in rooms_data:
            beds = room_data.pop('beds')
            
            # Create room
            room = Room.objects.create(**room_data)
            total_rooms += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Created Room: {room.room_number} - {room.get_room_type_display()} (Rs. {room.daily_rate}/day)'
                )
            )
            
            # Create beds for this room
            for bed_number in beds:
                Bed.objects.create(
                    room=room,
                    bed_number=bed_number,
                    is_occupied=False
                )
                total_beds += 1
                self.stdout.write(f'  └─ Bed {bed_number} added')

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'\n✅ Setup Complete!'))
        self.stdout.write(self.style.SUCCESS(f'\n📊 Summary:'))
        self.stdout.write(f'   • Total Rooms Created: {total_rooms}')
        self.stdout.write(f'   • Total Beds Created: {total_beds}')
        self.stdout.write('\n📋 Room Types:')
        self.stdout.write(f'   • General Ward: 8 beds (Rs. 2000/day)')
        self.stdout.write(f'   • Private Rooms: 4 beds (Rs. 5000/day)')
        self.stdout.write(f'   • ICU: 5 beds (Rs. 10000/day)')
        self.stdout.write(f'   • Emergency: 4 beds (Rs. 7500/day)')
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('\n🚀 System is ready to use!\n'))
