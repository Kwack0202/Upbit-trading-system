# trend_combinations.py

trend_combinations = {
    # ---------------------------------------------------------
    # 단기 상승
    ('up', 'up', 'up'): 'up',
    ('up', 'up', 'sideway'): 'up',
    ('up', 'up', 'down'): 'up',
    
    ('up', 'sideway', 'up'): 'up',
    ('up', 'sideway', 'sideway'): 'up',
    ('up', 'sideway', 'down'): 'sideway',
    
    ('up', 'down', 'up'): 'up',
    ('up', 'down', 'sideway'): 'sideway',
    ('up', 'down', 'down'): 'down',
    
    # ---------------------------------------------------------
    # 단기 횡보
    ('sideway', 'up', 'up'): 'sideway',
    ('sideway', 'up', 'sideway'): 'sideway',
    ('sideway', 'up', 'down'): 'down',
    
    ('sideway', 'sideway', 'up'): 'sideway',
    ('sideway', 'sideway', 'sideway'): 'sideway',
    ('sideway', 'sideway', 'down'): 'sideway',
    
    ('sideway', 'down', 'up'): 'sideway',
    ('sideway', 'down', 'sideway'): 'sideway',
    ('sideway', 'down', 'down'): 'down',
    
    # ---------------------------------------------------------
    # 단기 하락
    ('down', 'up', 'up'): 'sideway',
    ('down', 'up', 'sideway'): 'sideway',
    ('down', 'up', 'down'): 'down',
    
    ('down', 'sideway', 'up'): 'down',
    ('down', 'sideway', 'sideway'): 'down',
    ('down', 'sideway', 'down'): 'down',
    
    ('down', 'down', 'up'): 'down',
    ('down', 'down', 'sideway'): 'down',
    ('down', 'down', 'down'): 'down',
}
