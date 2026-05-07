import os
import sys
import json
from flask import Flask, render_template, jsonify, request, redirect, url_for
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.config import Config
from scheduler.task_manager import TaskManager


def create_app(config_path=None):
    app = Flask(__name__)

    config = Config(config_path)
    web_config = config.get_web_admin_config()
    app.secret_key = web_config.get('secret_key', 'infopulse-secret-key')

    task_manager = TaskManager(config)

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/api/status')
    def get_status():
        status = task_manager.get_system_status()
        return jsonify(status)

    @app.route('/api/tasks')
    def get_tasks():
        tasks = task_manager.get_all_tasks()
        return jsonify(tasks)

    @app.route('/api/tasks/<source_name>')
    def get_task_detail(source_name):
        task = task_manager.get_task_detail(source_name)
        if task:
            return jsonify(task)
        return jsonify({'error': '任务不存在'}), 404

    @app.route('/api/tasks/<source_name>/pause', methods=['POST'])
    def pause_task(source_name):
        success = task_manager.pause_task(source_name)
        return jsonify({'success': success})

    @app.route('/api/tasks/<source_name>/resume', methods=['POST'])
    def resume_task(source_name):
        success = task_manager.resume_task(source_name)
        return jsonify({'success': success})

    @app.route('/api/tasks/<source_name>/run', methods=['POST'])
    def run_task(source_name):
        success = task_manager.run_task_now(source_name)
        return jsonify({'success': success})

    @app.route('/api/logs')
    def get_logs():
        source_name = request.args.get('source_name')
        limit = request.args.get('limit', 100, type=int)
        logs = task_manager.get_task_logs(source_name, limit)
        return jsonify(logs)

    @app.route('/api/statistics')
    def get_statistics():
        stats = task_manager.get_task_statistics()
        return jsonify(stats)

    @app.route('/api/sources')
    def get_sources():
        sources = task_manager.get_source_configs()
        return jsonify(sources)

    @app.route('/api/sources/<name>', methods=['GET'])
    def get_source(name):
        sources = task_manager.get_source_configs()
        for source in sources:
            if source.get('name') == name:
                return jsonify(source)
        return jsonify({'error': '采集源不存在'}), 404

    @app.route('/api/sources', methods=['POST'])
    def add_source():
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的数据'}), 400
        success = task_manager.add_source_config(data)
        return jsonify({'success': success})

    @app.route('/api/sources/<name>', methods=['PUT'])
    def update_source(name):
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的数据'}), 400
        data['name'] = name
        success = task_manager.update_source_config(name, data)
        return jsonify({'success': success})

    @app.route('/api/sources/<name>', methods=['DELETE'])
    def delete_source(name):
        success = task_manager.delete_source_config(name)
        return jsonify({'success': success})

    @app.route('/api/reload', methods=['POST'])
    def reload_config():
        success = task_manager.reload_scheduler()
        return jsonify({'success': success})

    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')

    @app.route('/tasks')
    def tasks_page():
        return render_template('tasks.html')

    @app.route('/logs')
    def logs_page():
        return render_template('logs.html')

    @app.route('/sources')
    def sources_page():
        return render_template('sources.html')

    @app.route('/news')
    def news_page():
        return render_template('news.html')

    return app