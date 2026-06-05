from datetime import datetime


def current_year(request):
    return {"current_year": datetime.now().year}


def cart_count(request):
    cart = request.session.get('cart', {})
    count = sum(int(item['qty']) for item in cart.values())
    return {"cart_count": count}
