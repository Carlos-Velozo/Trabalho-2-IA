import math
import random
import copy
import time

# =====================================================================
# PARTE 1: REPRESENTAÇÃO DO ESTADO, REGRAS E TABULEIRO (Othello/Reversi)
# =====================================================================
class Othello:
    def __init__(self, size=6):
        """
        Inicializa o estado do jogo. 
        Por padrão o tabuleiro é 6x6, mas aceita 7x7 (modificação não trivial exigida).
        Convenção: 
          1  -> Jogador 1 (Preto)
         -1  -> Jogador 2 (Branco / Oponente)
          0  -> Espaço Vazio
        """
        self.size = size
        # Cria a matriz (lista de listas) preenchida com zeros
        self.board = [[0 for _ in range(size)] for _ in range(size)]
        
        # Encontra o meio do tabuleiro para posicionar as 4 peças iniciais
        mid = size // 2
        
        # Lógica para posicionamento inicial
        # Se for par (ex: 6x6), o centro é exato. Se for ímpar (ex: 7x7), 
        # deslocamos o bloco 2x2 levemente para o centro superior esquerdo.
        self.board[mid-1][mid-1] = -1
        self.board[mid][mid] = -1
        self.board[mid-1][mid] = 1
        self.board[mid][mid-1] = 1

    def is_valid_move(self, r, c, player):
        """
        Verifica se colocar uma peça na linha 'r' e coluna 'c' é uma jogada válida.
        Regra: A peça deve flanquear (encurralar) pelo menos uma peça adversária.
        """
        # Se a casa não estiver vazia, a jogada é inválida
        if self.board[r][c] != 0:
            return False
        
        # As 8 direções ao redor de uma casa: (linha, coluna)
        # Cima, Baixo, Esquerda, Direita e as 4 Diagonais
        directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            found_opponent = False
            
            # Anda na direção escolhida enquanto estiver dentro dos limites do tabuleiro
            while 0 <= nr < self.size and 0 <= nc < self.size:
                if self.board[nr][nc] == -player:
                    # Achamos uma peça do oponente, continuamos olhando na mesma direção
                    found_opponent = True
                elif self.board[nr][nc] == player:
                    # Achamos uma peça nossa. Se achamos oponente antes, o flanco está fechado! (Válida)
                    if found_opponent: return True
                    # Se não tinha oponente no meio, não serve. Para de olhar essa direção.
                    break
                else:
                    # Achamos um espaço vazio. Flanco quebrado. Para de olhar essa direção.
                    break
                
                # Continua andando na mesma direção
                nr += dr
                nc += dc
                
        # Se checou todas as direções e não fechou nenhum flanco, é inválida.
        return False

    def get_valid_moves(self, player):
        """Geração de jogadas válidas: retorna uma lista com todas as coordenadas (r, c) permitidas."""
        moves = []
        for r in range(self.size):
            for c in range(self.size):
                if self.is_valid_move(r, c, player):
                    moves.append((r, c))
        return moves

    def make_move(self, move, player):
        """
        Atualização do tabuleiro e regras de captura.
        Aplica a jogada (r,c) no tabuleiro e vira (captura) as peças do oponente.
        """
        r, c = move
        self.board[r][c] = player # Coloca a peça
        
        directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            pieces_to_flip = []
            
            # Procura peças para virar nesta direção
            while 0 <= nr < self.size and 0 <= nc < self.size:
                if self.board[nr][nc] == -player:
                    # Anota a coordenada da peça do oponente para virar depois
                    pieces_to_flip.append((nr, nc))
                elif self.board[nr][nc] == player:
                    # Achamos a nossa peça fechando o flanco! Vira todas as anotadas.
                    for fr, fc in pieces_to_flip:
                        self.board[fr][fc] = player
                    break
                else:
                    # Espaço vazio quebra a sequência. Não vira nada.
                    break
                nr += dr
                nc += dc

    def is_terminal(self):
        """Condição de término: o jogo acaba quando NENHUM dos jogadores tem jogadas válidas."""
        # Se a lista de movimentos de ambos for vazia (tamanho 0), o jogo acabou.
        return len(self.get_valid_moves(1)) == 0 and len(self.get_valid_moves(-1)) == 0

    def get_winner(self):
        """Cálculo do vencedor: conta quem tem mais peças no tabuleiro."""
        score_1 = sum(row.count(1) for row in self.board)
        score_minus_1 = sum(row.count(-1) for row in self.board)
        
        if score_1 > score_minus_1: return 1
        elif score_minus_1 > score_1: return -1
        return 0 # Empate
    
    def print_board(self):
        """Função auxiliar para desenhar o tabuleiro no terminal."""
        symbols = {1: 'P', -1: 'B', 0: '.'}
        for row in self.board:
            print(" ".join([symbols[x] for x in row]))
        print("")


# =====================================================================
# PARTE 2: AGENTE MIN-MAX COM PODA ALFA-BETA E HEURÍSTICA
# =====================================================================
class MinMaxAgent:
    def __init__(self, player, depth):
        self.player = player # Qual cor o agente está controlando (1 ou -1)
        self.depth = depth   # Profundidade limitada (ex: 3 a 5 níveis)

    def evaluate(self, game):
        """
        Função de Avaliação Heurística no formato: Avaliar(s) = sum(wi * fi(s)).
        Usa três características cruciais para medir quem está ganhando.
        """
        # Característica 3: Diferença de Peças (Peso w3 = 1)
        my_pieces = sum(row.count(self.player) for row in game.board)
        opp_pieces = sum(row.count(-self.player) for row in game.board)
        f3_diff = my_pieces - opp_pieces 
        
        # Característica 2: Mobilidade (Peso w2 = 10)
        # Ter mais jogadas disponíveis significa ditar o ritmo do jogo.
        my_moves = len(game.get_valid_moves(self.player))
        opp_moves = len(game.get_valid_moves(-self.player))
        f2_mobility = my_moves - opp_moves
        
        # Característica 1: Controle de Cantos (Peso w1 = 50)
        # Cantos não podem ser virados, garantem estabilidade.
        corners = [(0,0), (0, game.size-1), (game.size-1, 0), (game.size-1, game.size-1)]
        my_corners = sum(1 for r, c in corners if game.board[r][c] == self.player)
        opp_corners = sum(1 for r, c in corners if game.board[r][c] == -self.player)
        f1_corners = my_corners - opp_corners 
        
        # Retorna o cálculo final da heurística
        return 50 * f1_corners + 10 * f2_mobility + 1 * f3_diff

    def get_move(self, game):
        """Inicia a busca na árvore de decisão para encontrar a melhor jogada."""
        best_val = -math.inf
        best_move = None
        
        # Valores iniciais de alfa (melhor para MAX) e beta (melhor para MIN)
        alpha = -math.inf
        beta = math.inf
        
        moves = game.get_valid_moves(self.player)
        if not moves: return None # Passa a vez
        
        # Para cada jogada possível na raiz, inicia a recursão
        for move in moves:
            new_game = copy.deepcopy(game) # Simula o tabuleiro
            new_game.make_move(move, self.player)
            
            # Como a vez agora é do oponente, chama o min_value
            val = self.min_value(new_game, self.depth - 1, alpha, beta)
            
            if val > best_val:
                best_val = val
                best_move = move
            # Atualiza o alfa propagado
            alpha = max(alpha, best_val)
            
        return best_move

    def max_value(self, game, depth, alpha, beta):
        """Nó MAX: Tenta encontrar o maior valor possível para o agente."""
        # Critério de parada: fim do jogo ou atingiu a profundidade máxima (níveis)
        if game.is_terminal() or depth == 0: 
            return self.evaluate(game) # Retorna a heurística calculada
            
        v = -math.inf
        moves = game.get_valid_moves(self.player)
        
        # Se não tem jogadas, passa a vez e deixa o MIN jogar
        if not moves: 
            return self.min_value(game, depth - 1, alpha, beta) 
        
        for move in moves:
            new_game = copy.deepcopy(game)
            new_game.make_move(move, self.player)
            v = max(v, self.min_value(new_game, depth - 1, alpha, beta))
            
            # PODA ALFA-BETA: 
            # Se v for maior ou igual ao beta do MIN, o MIN nunca vai deixar 
            # chegar aqui. Podemos ignorar o resto das jogadas deste ramo.
            if v >= beta: 
                return v 
                
            alpha = max(alpha, v) # Atualiza o alfa
        return v

    def min_value(self, game, depth, alpha, beta):
        """Nó MIN: Simula o oponente tentando nos prejudicar (menor valor possível)."""
        if game.is_terminal() or depth == 0: 
            return self.evaluate(game)
            
        v = math.inf
        moves = game.get_valid_moves(-self.player)
        
        if not moves: 
            return self.max_value(game, depth - 1, alpha, beta)
        
        for move in moves:
            new_game = copy.deepcopy(game)
            new_game.make_move(move, -self.player)
            v = min(v, self.max_value(new_game, depth - 1, alpha, beta))
            
            # PODA ALFA-BETA: 
            # Se v for menor ou igual ao alfa do MAX, o MAX não vai escolher
            # esse caminho (pois ele já tem algo melhor garantido em alfa). Poda!
            if v <= alpha: 
                return v 
                
            beta = min(beta, v) # Atualiza o beta
        return v


# =====================================================================
# PARTE 3: AGENTE MONTE CARLO TREE SEARCH (MCTS)
# =====================================================================
class MCTSNode:
    """Representa um nó na árvore de busca do MCTS."""
    def __init__(self, state, player, parent=None, move=None):
        self.state = state         # O estado do tabuleiro neste nó
        self.player = player       # De quem é a vez de jogar a partir deste estado
        self.parent = parent       # Nó pai (necessário para a retropropagação)
        self.move = move           # Qual jogada gerou este nó
        self.children = []         # Lista de nós filhos (próximos estados)
        self.wins = 0              # Quantidade de vitórias simuladas que passaram por aqui
        self.visits = 0            # Quantas vezes este nó foi visitado
        self.untried_moves = state.get_valid_moves(player) # Jogadas não testadas

    def UCT_select_child(self):
        """
        SELEÇÃO: Escolhe o melhor filho usando a fórmula UCT.
        UCT = (vitórias/visitas) + c * sqrt(ln(visitas_do_pai) / visitas_do_filho)
        Equilibra a 'explotação' (jogadas boas) com 'exploração' (jogadas não visitadas).
        """
        c = math.sqrt(2) # Constante de exploração teórica
        best_child = max(self.children, key=lambda n: 
            (n.wins / n.visits) + c * math.sqrt(math.log(self.visits) / n.visits))
        return best_child

    def expand(self):
        """
        EXPANSÃO: Pega uma jogada não testada, aplica no estado e cria um novo nó filho.
        """
        move = self.untried_moves.pop() # Tira uma jogada da lista de não testadas
        new_state = copy.deepcopy(self.state)
        new_state.make_move(move, self.player)
        
        # Cria o nó filho (trocando a vez do jogador)
        child_node = MCTSNode(new_state, -self.player, self, move)
        self.children.append(child_node)
        return child_node

    def update(self, result):
        """
        RETROPROPAGAÇÃO: Atualiza os dados deste nó baseando-se no resultado da simulação.
        """
        self.visits += 1
        # Atenção: a vitória conta para o jogador que FEZ a jogada para CHEGAR neste nó 
        # (ou seja, o oponente do jogador que vai jogar agora -self.player).
        if result == -self.player: 
            self.wins += 1 

class MCTSAgent:
    def __init__(self, player, simulations):
        self.player = player
        self.simulations = simulations # Limite de iterações/rollouts

    def get_move(self, game):
        """Roda o ciclo do MCTS para decidir a melhor jogada."""
        root = MCTSNode(game, self.player)
        moves = game.get_valid_moves(self.player)
        if not moves: return None

        # Roda o número definido de simulações (Critério de parada por quantidade)
        for _ in range(self.simulations):
            node = root
            state = copy.deepcopy(game)
            
            # 1. SELEÇÃO: Desce a árvore por nós já totalmente expandidos
            while node.untried_moves == [] and node.children != []:
                node = node.UCT_select_child()
                state.make_move(node.move, -node.player) 
            
            # 2. EXPANSÃO: Se o nó tem jogadas virgens, cria UM novo filho
            if node.untried_moves != []:
                node = node.expand()
                state.make_move(node.move, -node.player)
                
            # 3. SIMULAÇÃO (Rollout Estratégia Aleatória): 
            # A partir do novo estado, joga aleatoriamente até o final do jogo
            current_player = node.player
            while not state.is_terminal():
                valid_moves = state.get_valid_moves(current_player)
                if valid_moves:
                    action = random.choice(valid_moves) # Escolha randômica
                    state.make_move(action, current_player)
                current_player = -current_player # Alterna turno
            
            # 4. RETROPROPAGAÇÃO: Vê quem ganhou e sobe a árvore anotando
            winner = state.get_winner()
            while node is not None:
                node.update(winner)
                node = node.parent

        # Após todas as simulações, o resultado final é simplesmente 
        # escolher o nó filho a partir da raiz que foi MAIS visitado (mais confiável).
        return max(root.children, key=lambda c: c.visits).move


# =====================================================================
# PARTE 4: EXPERIMENTAÇÃO E MENU DE TESTES
# =====================================================================
def play_game(agent1, agent2, size, debug=False):
    """Controla uma única partida entre dois agentes até o fim."""
    game = Othello(size)
    current_player = 1 # O Preto (1) sempre começa no Othello
    
    while not game.is_terminal():
        moves = game.get_valid_moves(current_player)
        
        if not moves:
            # Se o jogador não tem movimentos, passa o turno (regra do Othello)
            current_player = -current_player
            continue
            
        # Pede a jogada para o agente correspondente ao turno atual
        if current_player == 1:
            move = agent1.get_move(game)
        else:
            move = agent2.get_move(game)
            
        if move:
            game.make_move(move, current_player)
            if debug:
                print(f"Jogador {'P (1)' if current_player == 1 else 'B (-1)'} jogou em {move}")
                game.print_board()
                
        current_player = -current_player # Troca o turno
        
    return game.get_winner()

def run_experiment(agent1_class, arg1, agent2_class, arg2, size, games=10):
    """
    Roda um lote de partidas para análise estatística de Taxa de Vitória.
    Compara o desempenho e o custo computacional (tempo).
    """
    print(f"\nIniciando Experimento: {games} partidas no tabuleiro {size}x{size}...")
    wins_1, wins_2, draws = 0, 0, 0
    start_time = time.time()
    
    for i in range(games):
        # Para ser justo na estatística, os agentes alternam quem é o Jogador 1 (que começa)
        p1 = 1 if i % 2 == 0 else -1
        p2 = -1 if i % 2 == 0 else 1
        
        # Instancia os agentes (ex: MinMaxAgent(1, 3) e MCTSAgent(-1, 200))
        a1 = agent1_class(p1, arg1)
        a2 = agent2_class(p2, arg2)
        
        # Quem foi sorteado para ser o 1 joga como primeiro parâmetro
        winner = play_game(a1 if p1 == 1 else a2, a2 if p1 == 1 else a1, size)
        
        if winner == p1: wins_1 += 1
        elif winner == p2: wins_2 += 1
        else: draws += 1
        print(f"Partida {i+1}/{games} concluída. Vencedor: {'Agente 1' if winner==p1 else 'Agente 2' if winner==p2 else 'Empate'}")
        
    end_time = time.time()
    print("\n================ RESULTADOS ================")
    print(f"Tempo Total de Execução: {end_time - start_time:.2f} segundos")
    print(f"Agente 1 ({agent1_class.__name__} config={arg1}): {wins_1} vitórias")
    print(f"Agente 2 ({agent2_class.__name__} config={arg2}): {wins_2} vitórias")
    print(f"Empates: {draws}")
    print("============================================")

def menu():
    """Interface interativa exigida para o professor testar as configurações."""
    while True:
        print("\n--- TRABALHO DE IA: OTHELLO (MINMAX E MCTS) ---")
        print("1. Jogar Min-Max vs MCTS (1 Partida com visualização passo a passo)")
        print("2. Análise: Impacto da Profundidade (MinMax depth 3 vs depth 5)")
        print("3. Análise: Impacto de Simulações (MCTS 50 vs 200)")
        print("4. Análise: Min-Max vs MCTS (Bateria de 10 Partidas)")
        print("5. Sair")
        
        escolha = input("Selecione uma opção (1-5): ")
        if escolha == '5': 
            print("Encerrando o programa.")
            break
            
        if escolha not in ['1', '2', '3', '4']:
            print("Opção inválida.")
            continue
        
        size_input = input("Tamanho do tabuleiro (6 para original, 7 para modificado): ")
        size = 7 if size_input == '7' else 6
        
        if escolha == '1':
            a1 = MinMaxAgent(1, depth=3)
            a2 = MCTSAgent(-1, simulations=200)
            winner = play_game(a1, a2, size, debug=True)
            print(f"\nVencedor final: {winner} (1 = Min-Max, -1 = MCTS, 0 = Empate)")
            
        elif escolha == '2':
            # Compara duas instâncias do MinMax com profundidades diferentes
            run_experiment(MinMaxAgent, 3, MinMaxAgent, 5, size, games=10)
            
        elif escolha == '3':
            # Compara duas instâncias do MCTS com números de simulações diferentes
            run_experiment(MCTSAgent, 50, MCTSAgent, 200, size, games=10)
            
        elif escolha == '4':
            # Compara os dois algoritmos diretamente
            run_experiment(MinMaxAgent, 3, MCTSAgent, 200, size, games=10)

if __name__ == "__main__":
    menu()