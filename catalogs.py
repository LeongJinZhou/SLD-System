"""Controlled choices from the United Nations Sustainable Development Goals."""
SDGS = [
    {'id': str(index), 'name': name}
    for index, name in enumerate([
        'No Poverty', 'Zero Hunger', 'Good Health and Well-being', 'Quality Education',
        'Gender Equality', 'Clean Water and Sanitation', 'Affordable and Clean Energy',
        'Decent Work and Economic Growth', 'Industry, Innovation and Infrastructure',
        'Reduced Inequalities', 'Sustainable Cities and Communities',
        'Responsible Consumption and Production', 'Climate Action', 'Life Below Water',
        'Life on Land', 'Peace, Justice and Strong Institutions', 'Partnerships for the Goals'
    ], 1)
]
