from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import uuid
import json
from datetime import datetime

# 初始化Flask应用
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'  # 上传文件存储目录
app.config['ANNOTATION_FOLDER'] = 'annotations'  # 标注结果存储目录

# 创建必要目录（Trae中自动创建）
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['ANNOTATION_FOLDER'], exist_ok=True)

# 情感标签库（可扩展）
EMOTION_LABELS = ["快乐", "悲伤", "愤怒", "恐惧", "中性", "惊喜"]

# 首页路由（渲染标注界面）
@app.route('/')
def index():
    return render_template('index.html', emotions=EMOTION_LABELS)

# 文件上传接口
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['media']
    if file:
        # 生成唯一文件名，避免重复
        filename = str(uuid.uuid4()) + "_" + file.filename
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        return jsonify({"file_url": f"/uploads/{filename}", "filename": file.filename})
    return jsonify({"error": "上传失败，请选择文件"}), 400

# 保存标注结果接口
@app.route('/save', methods=['POST'])
def save_annotation():
    data = request.json
    # 生成标注ID和时间戳
    data['annotation_id'] = str(uuid.uuid4())
    data['annotate_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 保存为JSON文件
    save_path = os.path.join(app.config['ANNOTATION_FOLDER'], f"{data['annotation_id']}.json")
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return jsonify({"status": "success", "annotation_id": data['annotation_id'], "file_path": save_path})

# 静态资源访问（上传的音视频）
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    # Trae中使用0.0.0.0和端口5000，自动映射
    app.run(debug=True, host='0.0.0.0', port=5000)