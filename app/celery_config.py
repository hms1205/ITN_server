from celery import Celery

# Celery 애플리케이션 초기화
celery_app = Celery(
    "tasks", broker="redis://127.0.0.1:6379/0", backend="redis://127.0.0.1:6379/0"
)

celery_app.conf.update(
    result_expires=3600,  # 작업 결과의 만료 시간
)
