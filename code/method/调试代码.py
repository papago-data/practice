import pygame
import random
from collections import deque  # 用于BFS寻路算法

# --- 1. 初始化设置 ---
pygame.init()

# 颜色定义 (R, G, B)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (213, 50, 80)
GREEN = (0, 255, 0)
BLUE = (50, 153, 213)

# 屏幕尺寸
DIS_WIDTH = 600
DIS_HEIGHT = 400

# 创建显示窗口
dis = pygame.display.set_mode((DIS_WIDTH, DIS_HEIGHT))
pygame.display.set_caption('贪吃蛇游戏 - 随机迷宫版')

clock = pygame.time.Clock()

# 蛇的参数
SNAKE_BLOCK = 10  # 蛇身和障碍物每一格的大小

# 字体设置
font_style = pygame.font.SysFont("bahnschrift", 25)
score_font = pygame.font.SysFont("comicsansms", 35)

# --- 2. 辅助函数 ---

# 动态速度计算函数
BASE_SPEED = 10       
SPEED_INCREMENT = 0.5 

def get_current_speed(length):
    return BASE_SPEED + (length - 1) * SPEED_INCREMENT

# 显示分数
def your_score(score):
    value = score_font.render("Score: " + str(score), True, WHITE)
    dis.blit(value, [0, 0])

# 绘制蛇
def our_snake(snake_block, snake_list):
    for x in snake_list:
        pygame.draw.rect(dis, GREEN, [x[0], x[1], snake_block, snake_block])

# 绘制障碍物
def draw_obstacles(obstacles_list):
    for obs in obstacles_list:
        pygame.draw.rect(dis, BLUE, [obs[0], obs[1], SNAKE_BLOCK, SNAKE_BLOCK])

# 显示消息
def message(msg, color):
    mesg = font_style.render(msg, True, color)
    text_rect = mesg.get_rect(center=(DIS_WIDTH/2, DIS_HEIGHT/2))
    dis.blit(mesg, text_rect)

# 【核心新增】随机生成障碍物函数
def generate_obstacles(num_obstacles=40):
    """
    生成随机障碍物，并保证地图是连通的（不会堵死玩家）
    """
    while True:
        obstacles = []
        # 获取地图的网格数量
        grid_w = DIS_WIDTH // SNAKE_BLOCK
        grid_h = DIS_HEIGHT // SNAKE_BLOCK
        
        # 在地图范围内随机生成障碍物
        for _ in range(num_obstacles):
            x = random.randint(0, grid_w - 1) * SNAKE_BLOCK
            y = random.randint(0, grid_h - 1) * SNAKE_BLOCK
            obstacles.append([x, y])
            
        # 1. 保护出生点：移除中心区域的障碍物
        safe_zone_x = DIS_WIDTH // 2
        safe_zone_y = DIS_HEIGHT // 2
        obstacles = [obs for obs in obstacles if obs != [safe_zone_x, safe_zone_y]]
        
        # 2. 连通性检测 (BFS算法)：确保左上角能走到右下角
        start = (0, 0)
        end = (DIS_WIDTH - SNAKE_BLOCK, DIS_HEIGHT - SNAKE_BLOCK)
        
        # 将障碍物转为 set 集合，加快查找速度
        obs_set = set(map(tuple, obstacles))
        
        visited = set()
        queue = deque([start])
        visited.add(start)
        directions = [(SNAKE_BLOCK, 0), (-SNAKE_BLOCK, 0), (0, SNAKE_BLOCK), (0, -SNAKE_BLOCK)]
        
        while queue:
            curr_x, curr_y = queue.popleft()
            if (curr_x, curr_y) == end:
                return obstacles  # 连通成功！直接返回障碍物列表
            
            for dx, dy in directions:
                nx, ny = curr_x + dx, curr_y + dy
                if (0 <= nx < DIS_WIDTH and 0 <= ny < DIS_HEIGHT and 
                    (nx, ny) not in visited and (nx, ny) not in obs_set):
                    visited.add((nx, ny))
                    queue.append((nx, ny))
        
        # 如果不连通，while True 会触发，重新生成一遍障碍物

# --- 3. 游戏主循环 ---
def gameLoop():
    game_over = False
    game_close = False

    # 初始位置（屏幕中心）
    x1 = DIS_WIDTH / 2
    y1 = DIS_HEIGHT / 2

    # 移动变化量
    x1_change = 0
    y1_change = 0

    # 蛇身列表
    snake_List = []
    Length_of_snake = 1

    # 【新增】每次开始游戏时，随机生成障碍物
    obstacles = generate_obstacles(40)  # 这里可以修改数字，40代表生成40个障碍物

    # 生成第一个食物（避开蛇和障碍物）
    while True:
        foodx = round(random.randrange(0, DIS_WIDTH - SNAKE_BLOCK) / 10.0) * 10.0
        foody = round(random.randrange(0, DIS_HEIGHT - SNAKE_BLOCK) / 10.0) * 10.0
        if [foodx, foody] not in obstacles and [foodx, foody] != [x1, y1]:
            break

    while not game_over:

        # 游戏结束时的循环
        while game_close == True:
            dis.fill(BLACK)
            message("C or Q", RED)
            your_score(Length_of_snake - 1)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        game_over = True
                        game_close = False
                    if event.key == pygame.K_c:
                        gameLoop() 

        # 处理按键事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    x1_change = -SNAKE_BLOCK
                    y1_change = 0
                elif event.key == pygame.K_RIGHT:
                    x1_change = SNAKE_BLOCK
                    y1_change = 0
                elif event.key == pygame.K_UP:
                    y1_change = -SNAKE_BLOCK
                    x1_change = 0
                elif event.key == pygame.K_DOWN:
                    y1_change = SNAKE_BLOCK
                    x1_change = 0

        # 检查是否撞墙
        if x1 >= DIS_WIDTH or x1 < 0 or y1 >= DIS_HEIGHT or y1 < 0:
            game_close = True

        # 检查是否撞到障碍物
        if [x1, y1] in obstacles:
            game_close = True

        # 更新位置
        x1 += x1_change
        y1 += y1_change
        dis.fill(BLACK) 

        # 画食物和障碍物
        pygame.draw.rect(dis, RED, [foodx, foody, SNAKE_BLOCK, SNAKE_BLOCK])
        draw_obstacles(obstacles)

        # 更新蛇身逻辑
        snake_Head = []
        snake_Head.append(x1)
        snake_Head.append(y1)
        snake_List.append(snake_Head)

        if len(snake_List) > Length_of_snake:
            del snake_List[0]

        # 检查是否撞到自己
        for x in snake_List[:-1]:
            if x == snake_Head:
                game_close = True

        our_snake(SNAKE_BLOCK, snake_List)
        your_score(Length_of_snake - 1)

        pygame.display.update()

        # 检查是否吃到食物
        if x1 == foodx and y1 == foody:
            Length_of_snake += 1
            # 重新生成食物，避开蛇和障碍物
            while True:
                foodx = round(random.randrange(0, DIS_WIDTH - SNAKE_BLOCK) / 10.0) * 10.0
                foody = round(random.randrange(0, DIS_HEIGHT - SNAKE_BLOCK) / 10.0) * 10.0
                if [foodx, foody] not in obstacles and [foodx, foody] not in snake_List:
                    break

        # 动态速度控制
        clock.tick(get_current_speed(Length_of_snake))

    pygame.quit()
    quit()

# 启动游戏
gameLoop()