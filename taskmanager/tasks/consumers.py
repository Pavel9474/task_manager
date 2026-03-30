import json
from channels.generic.websocket import AsyncWebsocketConsumer

class TaskConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.room_group_name = f'task_{self.task_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        
        # Отправляем всем в группе
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'task_update',
                'data': data
            }
        )
    
    async def task_update(self, event):
        # Отправляем клиенту
        await self.send(text_data=json.dumps(event['data']))