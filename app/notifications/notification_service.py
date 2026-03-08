import os
import requests
import json
from typing import Dict, Optional
from app.config.type_manager import type_manager
from dotenv import load_dotenv

load_dotenv()


NOTIFICATION_TEMPLATES = {
    "wechat_message": {
        "title": "新留言通知",
        "description_template": "来自 {name} 的留言：{content}",
        "url_template": "{admin_url}"
    },
    "wechat_feedback": {
        "title": "新反馈通知",
        "description_template": "项目 {project_name} 收到新反馈：{content}",
        "url_template": "{admin_url}/feedback"
    },
    "wechat_notification": {
        "title": "{title}",
        "description_template": "{content}",
        "url_template": "{admin_url}"
    }
}


def send_notification(entry_type: str, metadata: Dict, source: Optional[str] = None):
    """发送通知"""
    # 获取类型的通知配置
    notification_config = type_manager.get_notification_config(entry_type)
    
    if not notification_config or not notification_config.get('enabled'):
        return
    
    template_name = notification_config.get('template')
    if not template_name or template_name not in NOTIFICATION_TEMPLATES:
        return
    
    # 发送企业微信通知
    send_wechat_notification(template_name, metadata)


def send_wechat_notification(template_name: str, metadata: Dict):
    """发送企业微信通知"""
    try:
        CORPID = os.getenv('CORPID')
        AGENTID = os.getenv('AGENTID')
        CORPSECRET = os.getenv('CORPSECRET')
        ADMIN_URL = os.getenv('ADMINURL', 'https://admin.example.com')
        
        if not all([CORPID, AGENTID, CORPSECRET]):
            print('WeChat credentials not configured')
            return
        
        # 获取access_token
        get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={CORPID}&corpsecret={CORPSECRET}"
        response = requests.get(get_token_url).content
        access_token = json.loads(response).get('access_token')
        
        if not access_token:
            print('Failed to get WeChat access token')
            return
        
        # 获取模板
        template = NOTIFICATION_TEMPLATES[template_name]
        
        # 格式化消息
        title = template['title'].format(**metadata) if '{' in template['title'] else template['title']
        description = template['description_template'].format(**metadata)
        url = template['url_template'].format(admin_url=ADMIN_URL)
        
        # 发送消息
        send_msg_url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
        data = {
            "touser": '@all',
            "agentid": AGENTID,
            "msgtype": "textcard",
            "textcard": {
                "title": title,
                "description": description,
                "url": url,
                "btntxt": "查看详情"
            },
            "enable_id_trans": 0,
            "enable_duplicate_check": 0,
            "duplicate_check_interval": 1800
        }
        
        res = requests.post(send_msg_url, data=json.dumps(data))
        
        if res.status_code == 200:
            print(f'WeChat notification sent successfully: {template_name}')
        else:
            print(f'Failed to send WeChat notification: {res.status_code}')
    
    except Exception as e:
        print(f'Error sending WeChat notification: {str(e)}')

# Made with Bob
