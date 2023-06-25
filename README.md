# Homepage back-end

<p>
    <a href="https://www.chenmo1212.cn?f=github-backend" target="_blank">
        <img alt="GitHub Workflow Status" src="https://img.shields.io/badge/Backend-Portfolio's--backend-orange">
    </a>
    <a href="https://github.com/Chenmo1212/homepage_backend" target="_blank">
        <img alt="GitHub repo size" src="https://img.shields.io/github/repo-size/Chenmo1212/homepage_backend">
    </a>
    <a href="https://github.com/Chenmo1212/homepage_backend/issues" target="_blank">
        <img alt="Issues" src="https://img.shields.io/github/issues/Chenmo1212/homepage_backend" />
    </a>
    <a href="https://github.com/Chenmo1212/homepage_backend/pulls" target="_blank">
        <img alt="GitHub pull requests" src="https://img.shields.io/github/issues-pr/Chenmo1212/homepage_backend" />
    </a>
    <a href="/"><img src="https://vbr.wocr.tk/badge?page_id=Chenmo1212/homepage_backend.visitors&left_color=green&right_color=red" alt="Visitor" /></a>
    <a href="https://github.com/Chenmo1212/homepage_backend" target="_blank">
        <img alt="GitHub" src="https://img.shields.io/github/license/Chenmo1212/homepage_backend">
    </a>
<br/>
<br/>
    <a href="https://github.com/Chenmo1212/homepage_backend" target="_blank">
        <img alt="GitHub followers" src="https://img.shields.io/github/followers/pudongping?style=social">
    </a>
    <a href="https://github.com/Chenmo1212/homepage_backend" target="_blank">
        <img alt="GitHub forks" src="https://img.shields.io/github/forks/Chenmo1212/homepage_backend?style=social">
    </a>
    <a href="https://github.com/Chenmo1212/homepage_backend" target="_blank">
        <img alt="GitHub stars" src="https://img.shields.io/github/stars/Chenmo1212/homepage_backend?style=social">
    </a>
    <a href="https://github.com/Chenmo1212/homepage_backend" target="_blank">
        <img alt="GitHub watchers" src="https://img.shields.io/github/watchers/Chenmo1212/homepage_backend?style=social">
    </a>
</p>

## Description

This is my Portfolio's back-end repository, using the python based flask framework.

You can check my Portfolio [here](https://www.chenmo1212.cn?f=github-backend).

### REST API

The project follows the `REST API` architectural style, providing endpoints for various operations.

- `GET /messages`: Retrieves a list of messages for guests.
- `POST /messages`: Adds a new message.
- `GET /admin/messages`: Retrieves a list of messages for administration.
- `PUT /admin/messages/{messageId}/status`: Updates the status of a message.
- `DELETE /admin/messages/{messageId}`: Deletes a message.
- j`POST /admin/messages/delete`: Deletes multiple messages based on the provided list of IDs.

### Wechat Notification

This project used the enterprise WeChat application to send notifications to WeChat in real time. When a guest sends a new message, a enterprise WeChat notification will be sent. In the environment variables below, `CORPID`, `AGENTID`, `CORPSECRET` and `ADMINURL` are environment variables related to enterprise WeChat notifications. If you don’t need them, just comment them out.

- You can check [here](https://developer.work.weixin.qq.com/document/path/90236) to get more information about [Enterprise WeChat sends application messages](https://developer.work.weixin.qq.com/document/path/90236)

### Api test

This project used `pytest` as the api testing framework, and created a `test_api.py` file in the root directory.

All interfaces can be tested with the following command:

```cmd
pytest test_api.py
```

## Installation

1. Clone the repository:

   ```cmd
   git clone https://github.com/Chenmo1212/homepage_backend.git
   ```

2. Navigate to the project directory:

   ```cmd
   cd your-repository
   ```

3. Create virtual environment:

   ```cmd
   python -m venv venv
   ```

4. Install the dependencies after entering the virtual environment just created:

   ```cmd
   pip install -r requirements.txt
   ```

5. Set up the environment variables:

   - Create a `.env` file in the project root directory. 

   - Add the following environment variables:  

     ```
     FLASK_ENV=development
     CORPID=your-corporate-id
     AGENTID=your-agent-id
     CORPSECRET=your-corporate-secret
     ADMINURL=https://xxxxxxx
     ```

6. Set up the configure file for development environment:

   - Create a `config_development.py` file in the project root directory. 

   - Add the following variables:  

     ```python
     MONGO_URI=your-mongodb-uri
     ```

7. Run the application:

   ```cmd
   flask run
   ```

## Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue if you find a bug or have a suggestion for a new feature.

## License
This project is licensed under the MIT License.
