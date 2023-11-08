from celery import shared_task


@shared_task
def test_func1(x, y):
    return x + y


@shared_task
def test_func2(x, y):
    return x*y
