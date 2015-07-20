{
    'name' : 'Instant Messaging Group and notification',
    'version': '1.0',
    'summary': 'OpenERP Group Chat & Notification',
    'author': 'BizzAppDev',
    'sequence': '18',
    'category': 'Tools',
    'complexity': 'easy',
    'website': 'http://www.bizzappdev.com',
    'description':
        """
Instant Grop Messaging & Desktop Notification
=============================================
* Enable Mail Groups for group chat. And posting in Group chat will reach to all followers of the Group
* Group in conversation list
* Adding Desktop Notification when new conversation received

        """,
    'data': [
        "views/im_chat_group.xml",
        "im_chat_group_view.xml",
    ],
    'depends' : ['im_chat', 'mail'],
    'qweb': [],
    'images': ['images/combine.png'],
    'price': 19.99,
    'currency': 'EUR',
    'application': True,
    'installable': True,
    'auto_install': True,
}
