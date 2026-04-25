import math
import random
import copy
import time

# =====================================================================
# CONSTANTES GLOBAIS DO JOGO
# =====================================================================
JOGADOR_PRETO = 1
JOGADOR_BRANCO = -1
VAZIO = 0

# =====================================================================
# PARTE 1: REPRESENTAÇÃO DO ESTADO, REGRAS E TABULEIRO
# =====================================================================
class Othello:
    DIRECOES = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    
    def __init__(self, tamanho=6):
        self.tamanho = tamanho
        self.tabuleiro = [[VAZIO for _ in range(tamanho)] for _ in range(tamanho)]
        self._inicializar_posicoes_iniciais()

    def _inicializar_posicoes_iniciais(self):
        meio = self.tamanho // 2
        self.tabuleiro[meio - 1][meio - 1] = JOGADOR_BRANCO
        self.tabuleiro[meio][meio] = JOGADOR_BRANCO
        self.tabuleiro[meio - 1][meio] = JOGADOR_PRETO
        self.tabuleiro[meio][meio - 1] = JOGADOR_PRETO

    def jogada_e_valida(self, linha, coluna, jogador):
        """
        Verifica se colocar uma peça na linha 'r' e coluna 'c' é uma jogada válida.
        Regra: A peça deve flanquear (encurralar) pelo menos uma peça adversária.
        """
        if self.tabuleiro[linha][coluna] != VAZIO:
            return False
        
        for deslocamento_linha, deslocamento_coluna in self.DIRECOES:
            if self._existe_flanco(linha, coluna, deslocamento_linha, deslocamento_coluna, jogador):
                return True
        return False
    
    def _existe_flanco(self, linha, coluna, d_linha, d_coluna, jogador):
        l_alvo, c_alvo = linha + d_linha, coluna + d_coluna
        encontrou_oponente = False

        # Anda na direção escolhida enquanto estiver dentro dos limites do tabuleiro
        while 0 <= l_alvo < self.tamanho and 0 <= c_alvo < self.tamanho:
            peca_atual = self.tabuleiro[l_alvo][c_alvo]
            if peca_atual == -jogador:
                # Achamos uma peça do oponente, continuamos olhando na mesma direção
                encontrou_oponente = True
            elif peca_atual == jogador:
                # Achamos uma peça nossa. Se achamos oponente antes, o flanco está fechado! (Válida)
                return encontrou_oponente
            else:
                # Achamos um espaço vazio. Flanco quebrado. Para de olhar essa direção.
                break

            # Continua andando na mesma direção
            l_alvo += d_linha
            c_alvo += d_coluna

        # Se checou todas as direções e não fechou nenhum flanco, é inválida.
        return False

    def obter_jogadas_validas(self, jogador):
        moves = []
        for linha in range(self.tamanho):
            for coluna in range(self.tamanho):
                if self.jogada_e_valida(linha, coluna, jogador):
                    moves.append((linha, coluna))
        return moves

    def aplicar_jogada(self, jogada, jogador):
        """
        Aplica a jogada no tabuleiro e vira (captura) as peças do oponente.
        """
        linha, coluna = jogada
        self.tabuleiro[linha][coluna] = jogador # Coloca a peça
        
        for d_linha, d_coluna in self.DIRECOES:
            pecas_para_virar = []
            l_alvo, c_alvo = linha + d_linha, coluna + d_coluna

            while 0 <= l_alvo < self.tamanho and 0 <= c_alvo < self.tamanho:
                if self.tabuleiro[l_alvo][c_alvo] == -jogador:
                    # Achamos uma peça do oponente, anotamos para virar depois
                    pecas_para_virar.append((l_alvo, c_alvo))
                elif self.tabuleiro[l_alvo][c_alvo] == jogador:
                    # Achamos uma peça nossa fechando o flanco! Vira todas as anotadas.
                    for l_virar, c_virar in pecas_para_virar:
                        self.tabuleiro[l_virar][c_virar] = jogador
                    break
                else:
                    # Achamos um espaço vazio. Flanco quebrado. Para de olhar essa direção.
                    break

                l_alvo += d_linha
                c_alvo += d_coluna

    def jogo_terminou(self):
        """Condição de término: o jogo acaba quando NENHUM dos jogadores tem jogadas válidas."""
        return not self.obter_jogadas_validas(JOGADOR_PRETO) and not self.obter_jogadas_validas(JOGADOR_BRANCO)

    def obter_vencedor(self):
        """Cálculo do vencedor: conta quem tem mais peças no tabuleiro."""
        pontos_preto = sum(linha.count(JOGADOR_PRETO) for linha in self.tabuleiro)
        pontos_branco = sum(linha.count(JOGADOR_BRANCO) for linha in self.tabuleiro)
        
        if pontos_preto > pontos_branco: return JOGADOR_PRETO
        if pontos_branco > pontos_preto: return JOGADOR_BRANCO
        return VAZIO # Empate
    
    def imprimir_tabuleiro(self):
        simbolos = {JOGADOR_PRETO: 'P', JOGADOR_BRANCO: 'B', VAZIO: '.'}
        for linha in self.tabuleiro:
            print(" ".join([simbolos[x] for x in linha]))
        print("")

# =====================================================================
# PARTE 2: AGENTE MIN-MAX COM PODA ALFA-BETA 
# =====================================================================
class AgenteMinMax:
    PESO_CANTOS = 50
    PESO_MOBILIDADE = 10
    PESO_PECAS = 1

    def __init__(self, jogador, profundidade):
        self.jogador = jogador 
        self.profundidade = profundidade

    def _avaliar_estado(self, jogo):
        """
        Função de Avaliação Heurística no formato: Avaliar(s) = sum(wi * fi(s))
        Avalia o tabuleiro baseado em Peças, Mobilidade e Cantos.
         - f1: Controle de Cantos (Peso w1 = 50)
         - f2: Mobilidade (Peso w2 = 10)
         - f3: Diferença de Peças (Peso w3 = 1)
        """
    
        f1_cantos = self._calcular_controle_cantos(jogo)
        f2_mobilidade = self._calcular_diferenca_mobilidade(jogo)
        f3_pecas = self._calcular_diferenca_pecas(jogo)

        return (self.PESO_CANTOS * f1_cantos) + (self.PESO_MOBILIDADE * f2_mobilidade) + (self.PESO_PECAS * f3_pecas)

    def _calcular_diferenca_pecas(self, jogo):
        minhas = sum(linha.count(self.jogador) for linha in jogo.tabuleiro)
        inimigo = sum(linha.count(-self.jogador) for linha in jogo.tabuleiro)
        return minhas - inimigo

    def _calcular_diferenca_mobilidade(self, jogo):
        minhas = len(jogo.obter_jogadas_validas(self.jogador))
        inimigo = len(jogo.obter_jogadas_validas(-self.jogador))
        return minhas - inimigo

    def _calcular_controle_cantos(self, jogo):
        tamanho = jogo.tamanho
        cantos = [(0,0), (0, tamanho-1), (tamanho-1, 0), (tamanho-1, tamanho-1)]
        meus = sum(1 for l, c in cantos if jogo.tabuleiro[l][c] == self.jogador)
        inimigo = sum(1 for l, c in cantos if jogo.tabuleiro[l][c] == -self.jogador)
        return meus - inimigo

    def obter_jogada(self, jogo):
        """Inicia a busca na árvore de decisão para encontrar a melhor jogada."""
        melhor_valor = -math.inf
        melhor_jogada = None
        alfa, beta = -math.inf, math.inf
        
        jogadas = jogo.obter_jogadas_validas(self.jogador)
        if not jogadas: return None 
        
        for jogada in jogadas:
            novo_jogo = copy.deepcopy(jogo) 
            novo_jogo.aplicar_jogada(jogada, self.jogador)
            
            valor = self._valor_minimo(novo_jogo, self.profundidade - 1, alfa, beta)
            
            if valor > melhor_valor:
                melhor_valor = valor
                melhor_jogada = jogada
            alfa = max(alfa, melhor_valor)
            
        return melhor_jogada

    def _valor_maximo(self, jogo, profundidade, alfa, beta):
        """Nó MAX: Tenta encontrar o maior valor possível para o agente."""

        # Critério de parada: fim do jogo ou atingiu a profundidade máxima (níveis)
        if jogo.jogo_terminou() or profundidade == 0: return self._avaliar_estado(jogo)
            
        v = -math.inf
        jogadas = jogo.obter_jogadas_validas(self.jogador)

        # Se não tem jogadas, passa a vez e deixa o MIN jogar
        if not jogadas: return self._valor_minimo(jogo, profundidade - 1, alfa, beta) 
        
        for jogada in jogadas:
            novo_jogo = copy.deepcopy(jogo)
            novo_jogo.aplicar_jogada(jogada, self.jogador)
            v = max(v, self._valor_minimo(novo_jogo, profundidade - 1, alfa, beta))

            # Regra: Se v for maior ou igual ao beta do MIN, o MIN nunca vai deixar chegar aqui. Podemos ignorar o resto das jogadas deste ramo.
            if v >= beta:
                return v 
            
            alfa = max(alfa, v) 
        return v

    def _valor_minimo(self, jogo, profundidade, alfa, beta):
        """Nó MIN: Simula o oponente tentando nos prejudicar (menor valor possível)."""

        # Critério de parada: fim do jogo ou atingiu a profundidade máxima (níveis)
        if jogo.jogo_terminou() or profundidade == 0: return self._avaliar_estado(jogo)
            
        v = math.inf
        jogadas = jogo.obter_jogadas_validas(-self.jogador)
        # Se não tem jogadas, passa a vez e deixa o MAX jogar
        if not jogadas: return self._valor_maximo(jogo, profundidade - 1, alfa, beta)
        
        for jogada in jogadas:
            novo_jogo = copy.deepcopy(jogo)
            novo_jogo.aplicar_jogada(jogada, -self.jogador)
            v = min(v, self._valor_maximo(novo_jogo, profundidade - 1, alfa, beta))
            # Regra: Se v for menor ou igual ao alfa do MAX, o MAX nunca vai deixar chegar aqui. Podemos ignorar o resto das jogadas deste ramo.
            if v <= alfa: return v 
            beta = min(beta, v) 
        return v

# =====================================================================
# PARTE 3: AGENTE MONTE CARLO TREE SEARCH (MCTS)
# =====================================================================
class NodoMCTS:
    CONSTANTE_EXPLORACAO = math.sqrt(2)

    """Representa um nó na árvore de busca do MCTS."""
    def __init__(self, estado, jogador, pai=None, jogada_geradora=None):
        self.estado = estado
        self.jogador_turno = jogador 
        self.pai = pai       
        self.jogada_geradora = jogada_geradora 
        self.filhos = []         
        self.vitorias = 0              
        self.visitas = 0            
        self.jogadas_nao_testadas = estado.obter_jogadas_validas(jogador)

    def selecionar_melhor_filho_uct(self):
        """
        SELEÇÃO: Escolhe o melhor filho usando a fórmula UCT.
        UCT = (vitórias/visitas) + c * sqrt(ln(visitas_do_pai) / visitas_do_filho)
        Equilibra a 'explotação' (jogadas boas) com 'exploração' (jogadas não visitadas).
        """
        return max(self.filhos, key=lambda n: (n.vitorias / n.visitas) + self.CONSTANTE_EXPLORACAO * math.sqrt(math.log(self.visitas) / n.visitas))

    def expandir(self):
        """
        EXPANSÃO: Pega uma jogada não testada, aplica no estado e cria um novo nó filho.
        """
        jogada = self.jogadas_nao_testadas.pop() 
        novo_estado = copy.deepcopy(self.estado)
        novo_estado.aplicar_jogada(jogada, self.jogador_turno)
        
        # Cria o nó filho (trocando a vez do jogador)
        novo_no = NodoMCTS(novo_estado, -self.jogador_turno, self, jogada)
        self.filhos.append(novo_no)
        return novo_no

    def retropropagar(self, resultado_vencedor):
        """
        RETROPROPAGAÇÃO: Atualiza os dados deste nó baseando-se no resultado da simulação.
        """
        self.visitas += 1
        # Atenção: a vitória conta para o jogador que FEZ a jogada para CHEGAR neste nó 
        # (ou seja, o oponente do jogador que vai jogar agora -self.player).
        if resultado_vencedor == -self.jogador_turno: 
            self.vitorias += 1

class AgenteMCTS:
    def __init__(self, jogador, simulacoes):
        self.jogador = jogador
        self.simulacoes = simulacoes

    def obter_jogada(self, jogo):
        """Roda o ciclo do MCTS para decidir a melhor jogada."""
        raiz = NodoMCTS(jogo, self.jogador)
        jogadas_iniciais = jogo.obter_jogadas_validas(self.jogador)
        if not jogadas_iniciais: return None

        # Roda o número definido de simulações (Critério de parada por quantidade)
        for _ in range(self.simulacoes):
            no_atual = raiz
            estado_simulado = copy.deepcopy(jogo)
            
            # 1. SELEÇÃO
            while not no_atual.jogadas_nao_testadas and no_atual.filhos:
                no_atual = no_atual.selecionar_melhor_filho_uct()
                estado_simulado.aplicar_jogada(no_atual.jogada_geradora, -no_atual.jogador_turno) 
            
            # 2. EXPANSÃO
            if no_atual.jogadas_nao_testadas:
                no_atual = no_atual.expandir()
                estado_simulado.aplicar_jogada(no_atual.jogada_geradora, -no_atual.jogador_turno)
                
            # 3. SIMULAÇÃO (Rollout)
            jogador_simulacao = no_atual.jogador_turno
            while not estado_simulado.jogo_terminou():
                jogadas = estado_simulado.obter_jogadas_validas(jogador_simulacao)
                if jogadas:
                    jogada_aleatoria = random.choice(jogadas)
                    estado_simulado.aplicar_jogada(jogada_aleatoria, jogador_simulacao)
                jogador_simulacao = -jogador_simulacao 
            
            # 4. RETROPROPAGAÇÃO
            vencedor = estado_simulado.obter_vencedor()
            while no_atual is not None:
                no_atual.retropropagar(vencedor)
                no_atual = no_atual.pai

        # Após todas as simulações, o resultado final é simplesmente 
        # escolher o nó filho a partir da raiz que foi MAIS visitado (mais confiável).
        melhor_filho = max(raiz.filhos, key=lambda c: c.visitas)
        return melhor_filho.jogada_geradora

# =====================================================================
# PARTE 4: EXPERIMENTAÇÃO E MENU DE TESTES
# =====================================================================
def jogar_partida(agente1, agente2, tamanho, debug=False):
    jogo = Othello(tamanho)
    jogador_atual = JOGADOR_PRETO 
    
    while not jogo.jogo_terminou():
        jogadas = jogo.obter_jogadas_validas(jogador_atual)
        
        if not jogadas:
            jogador_atual = -jogador_atual
            continue
            
        if jogador_atual == JOGADOR_PRETO:
            jogada = agente1.obter_jogada(jogo)
        else:
            jogada = agente2.obter_jogada(jogo)
            
        if jogada:
            jogo.aplicar_jogada(jogada, jogador_atual)
            if debug:
                print(f"Jogador {'P (1)' if jogador_atual == 1 else 'B (-1)'} jogou em {jogada}")
                jogo.imprimir_tabuleiro()
                
        jogador_atual = -jogador_atual 
        
    return jogo.obter_vencedor()

def rodar_experimento(classe_agente1, config1, classe_agente2, config2, tamanho, total_partidas=10):
    """
    Roda um lote de partidas para análise estatística de Taxa de Vitória.
    Compara o desempenho e o custo computacional (tempo).
    """
    print(f"\Iniciando Experimento: {total_partidas} partidas no tabuleiro {tamanho}x{tamanho}...")
    vitorias_1, vitorias_2, empates = 0, 0, 0
    inicio = time.time()
    
    for i in range(total_partidas):
        # Para ser justo na estatística, os agentes alternam quem é o Jogador 1 (que começa)
        cor_p1 = JOGADOR_PRETO if i % 2 == 0 else JOGADOR_BRANCO
        cor_p2 = JOGADOR_BRANCO if i % 2 == 0 else JOGADOR_PRETO
        
        # Instancia os agentes (ex: MinMaxAgent(1, 3) e MCTSAgent(-1, 200))
        a1 = classe_agente1(cor_p1, config1)
        a2 = classe_agente2(cor_p2, config2)
        
        # Quem foi sorteado para ser o JOGADOR_PRETO joga como primeiro parâmetro
        vencedor = jogar_partida(a1 if cor_p1 == JOGADOR_PRETO else a2, a2 if cor_p1 == JOGADOR_PRETO else a1, tamanho)
        
        if vencedor == cor_p1: vitorias_1 += 1
        elif vencedor == cor_p2: vitorias_2 += 1
        else: empates += 1
        print(f"Partida {i+1}/{total_partidas} concluída. Vencedor: {'Agente 1' if vencedor==cor_p1 else 'Agente 2' if vencedor==cor_p2 else 'Empate'}")
        
    fim = time.time()
    print("\n================ RESULTADOS ================")
    print(f"Tempo Total de Execução: {fim - inicio:.2f} segundos")
    print(f"Agente 1 ({classe_agente1.__name__} config={config1}): {vitorias_1} vitórias")
    print(f"Agente 2 ({classe_agente2.__name__} config={config2}): {vitorias_2} vitórias")
    print(f"Empates: {empates}")
    print("============================================")


def menu_principal():
    while True:
        print("\n--- TRABALHO DE IA: OTHELLO ---")
        print("1. Min-Max vs MCTS (1 Partida com debug)")
        print("2. Impacto da Profundidade (MinMax prof 3 vs prof 5)")
        print("3. Impacto de Simulações (MCTS 50 vs 200)")
        print("4. Min-Max vs MCTS (Bateria de 10 Partidas)")
        print("5. Sair")
        
        escolha = input("Selecione uma opção (1-5): ")
        if escolha == '5': break
            
        if escolha not in ['1', '2', '3', '4']:
            print("Opção inválida.")
            continue
        
        tamanho = int(input("Tamanho do tabuleiro (6 original, 7 modificado): "))
        
        if escolha == '1':
            a1 = AgenteMinMax(JOGADOR_PRETO, profundidade=3)
            a2 = AgenteMCTS(JOGADOR_BRANCO, simulacoes=200)
            vencedor = jogar_partida(a1, a2, tamanho, debug=True)
            print(f"\nVencedor final: {vencedor}")
            
        elif escolha == '2':
            rodar_experimento(AgenteMinMax, 3, AgenteMinMax, 5, tamanho, total_partidas=10)
            
        elif escolha == '3':
            rodar_experimento(AgenteMCTS, 50, AgenteMCTS, 200, tamanho, total_partidas=10)
            
        elif escolha == '4':
            rodar_experimento(AgenteMinMax, 3, AgenteMCTS, 200, tamanho, total_partidas=10)

if __name__ == "__main__":
    menu_principal()
    