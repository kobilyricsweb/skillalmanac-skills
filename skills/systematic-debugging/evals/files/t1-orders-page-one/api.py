from pager import paginate


def list_users(users, page=1, size=10):
    # public API pages count from 1
    return paginate(users, page - 1, size)


def list_orders(orders, page=1, size=10):
    # public API pages count from 1
    return paginate(orders, page, size)
