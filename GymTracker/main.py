import mysql.connector
from datetime import date

conexao = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="gymtracker"
)

cursor = conexao.cursor()

print("Banco conectado!")

exercicios_peito = [
    "Supino Reto", "Supino Inclinado","Crucifixo","Cross Over"
]
exercicios_costas = [
    "Puxada Frontal",
    "Remada Curvada",
    "Remada Baixa",
    "Pulldown"
]

exercicios_pernas = [
    "Agachamento",
    "Leg Press",
    "Cadeira Extensora",
    "Mesa Flexora"
]

exercicios_ombros = [
    "Desenvolvimento",
    "Elevação Lateral",
    "Elevação Frontal",
    "Remada Alta"
]

exercicios_biceps = [
    "Rosca Direta",
    "Rosca Alternada",
    "Rosca Martelo"
]

exercicios_triceps = [
    "Triceps Pulley",
    "Triceps Testa",
    "Triceps Banco"
]

def cadastrar_treino():
    print("Você escolheu Grupo Muscular")
    print("1 - Peito")
    print("2 - Costas")
    print("3 - Pernas")
    print("4 - Ombros")
    print("5 - Bíceps")
    print("6 - Tríceps")

    grupo = input("Escolha um grupo muscular: ")

    if grupo == "1":
        print("Exercícios de Peito")
#Peito
        for i, exercicio in enumerate(exercicios_peito, start=1):
            print(i, "-", exercicio)

        escolha = int(input("Escolha um exercicio: "))
        exercicio_escolhido = exercicios_peito[escolha - 1]

        carga = int(input("Digite a carga (kg): "))
        series = int(input("Digite o número de series: "))
        repeticoes = int(input("Digite o numero de repeticoes: "))
        data_treino = date.today()
 
        cursor.execute( 
             """
            INSERT INTO treinos
            (exercicio,carga,series,repeticoes, data_treino)
            VALUES(%s,%s,%s,%s,%s)""",
            (
                exercicio_escolhido,carga, series, repeticoes, data_treino)

            )
        conexao.commit()
        print("Treino salvo com Sucesso!")

    if grupo == "2":
        print("Exercícios de costas")
                #costas
        
        for i, exercicio in enumerate(exercicios_costas, start=1):
                    print(i, "-", exercicio)
        
        escolha = int(input("Escolha um exercicio: "))
        exercicio_escolhido = exercicios_costas[escolha - 1]
        
        carga = int(input("Digite a carga (kg): "))
        series = int(input("Digite o número de series: "))
        repeticoes = int(input("Digite o numero de repeticoes: "))
        data_treino = date.today()
        
                
        cursor.execute(
             
          """
          INSERT INTO treinos
          (exercicio, carga, series, repeticoes, data_treino)
          VALUES(%s,%s,%s,%s,%s)""",
          (
               
               exercicio_escolhido,carga,series,repeticoes,data_treino
          ) 
        )
        conexao.commit()
    
        print("Treino salvo com Sucesso!")  
        
        
    if grupo == "3":
         print("Exercicios de pernas")
         #pernas
         for i, exercicio in enumerate(exercicios_pernas, start=1):
          print(i,"-", exercicio) 
         escolha= int(input("Escolha um exercicio:"))
         exercicio_escolhido = exercicios_pernas[escolha -1]
         carga= int(input("Digite a carga (kg): " ))
         series = int(input( "Digite o numero de series: " )) 
         repeticoes = int(input("Digite o numero de repeticoes: "))
         data_treino = date.today()
         
         cursor.execute(
              """
              INSERT INTO treinos
              (exercicio, carga, series, repeticoes, data_treino)
              VALUES(%s,%s,%s,%s,%s)""",
              (

              exercicio_escolhido,carga, series,repeticoes, data_treino)
         )
         conexao.commit()
         print("Treino salvo com Sucesso!")
         
    if grupo == "4":
        print("Exercicios de ombros")
    #ombros
        for i, exercicio in enumerate(exercicios_ombros, start=1):
            print(i,"-", exercicio)
        escolha= int(input("Escolha um exercicio: "))
        exercicio_escolhido = exercicios_ombros[escolha - 1]
         
        carga= int(input("digite a carga (kg): "))
        series= int(input("Digite o numero de series: "))
        repeticoes= int(input("Digite o numero de repeticoes: "))
        data_treino = date.today()
        cursor.execute(
             """
             INSERT INTO treinos
             (exercicio, carga, series, repeticoes, data_treino)
             VALUES(%s,%s,%s,%s,%s)""",
             (exercicio_escolhido, carga, series, repeticoes, data_treino)
        )
        conexao.commit()
        print("Treino salvo com Sucesso!")
             
             
        
    if grupo == "5":
        print("Exercicio de Biceps")
              #biceps
        for i, exercicio in enumerate(exercicios_biceps,start=1):
            print(i,"-", exercicio)

        escolha=int(input("Escolha um exrercicio:"))
        exercicio_escolhido= exercicios_biceps[escolha -1]

        carga= int(input("Digite a carga (kg): "))
        series= int(input("Digite o numero de serie: "))
        repeticoes= int(input("Digite o numero de repeticoes:"))
        data_treino = date.today()
        cursor.execute(
             """
             INSERT INTO treinos
             (exercicio, carga, series, repeticoes, data_treino)
             VALUES(%s,%s,%s,%s,%s)
             """,
             (exercicio_escolhido, carga, series, repeticoes, data_treino)
        )
        conexao.commit()
        print("Treino salvo com Sucesso!")    
        
    if grupo =="6":
        print("Exercicio de Triceps")
         #Triceps
        for i, exercicio in enumerate(exercicios_triceps, start=1):
             print(i,"-", exercicio)

        escolha= int(input("Escolha um exercicio:"))
        exercicio_escolhido = exercicios_triceps[escolha  - 1]

        carga= int(input("Escolha a carga (kg): "))
        series= int(input("Escolha o numero de series: "))
        repeticoes= int(input("Escolha o numero de repeticoes"))
        data_treino = date.today()
        cursor.execute(
             """
             INSERT INTO treinos
             (exercicio, carga, series, repeticoes,data_treino)
             VALUES (%s,%s,%s,%s,%s)
             """,
             (exercicio_escolhido,carga,series,repeticoes, data_treino)
        )
        conexao.commit()
        print("Treino salvo com Sucesso!")
             
        
                          


    print("\n==== TREINO CADASTRADO ====")
def mostrar_treinos():
        print("\n=== TREINOS CADASTRADOS ===")

        cursor.execute("""
        SELECT id,exercicio, carga, series, repeticoes, data_treino
        FROM treinos
        """)
        treinos = cursor.fetchall()
        if len(treinos) == 0:
             print( "Nenhum treino cadastrado.")
             return
        for treino in treinos:
             print("\n------------------")
             print("ID:", treino[0])
             print("Exercicio:", treino [1])
             print("Carga:", treino[2],"kg")
             print("Series:", treino [3])
             print("Repeticoes:", treino [4])
             print("Data:", treino [5])
def excluir_treino():
     print("\n=== EXCLUIR TREINO ===")

     id_treino = int(input("Digite o ID do treino:"))

     cursor.execute(
          """
          DELETE FROM treinos
          WHERE id= %s
          """,
          (id_treino,)
     )
     conexao.commit()

     print("Treino excluido com Sucesso!")
def editar_treino():
     print("\n=== EDITAR TREINO ===")
     id_treino = int(input("digite o ID do treino:"))
     carga = int(input("Nova carga (kg):"))
     series = int(input("Novo numero de series:"))
     repeticoes = int(input("Novo numero de repeticoes:"))

     cursor.execute(
          """
          UPDATE treinos
          set carga = %s,
          series = %s,
          repeticoes= %s
          WHERE id = %s
          """,
          (carga,
           series,
           repeticoes,
           id_treino)
     )
     conexao.commit()
     print("treino atualizado com Sucesso!"
     )
def agendar_treino():
    print("\n=== AGENDAR TREINO ===")

    dia = input("Digite o dia da semana: ")
    grupo = input("Digite o grupo muscular: ")

    cursor.execute(
        """
        INSERT INTO agenda_treinos
        (dia_semana, grupo_muscular)
        VALUES (%s, %s)
        """,
        (
            dia,
            grupo
        )
    )

    conexao.commit()
    print("Treino agendado com sucesso!")
def ver_agenda():
    print("\n=== AGENDA DE TREINOS ===")

    cursor.execute("""
        SELECT dia_semana, grupo_muscular
        FROM agenda_treinos
    """)

    agenda = cursor.fetchall()

    if len(agenda) == 0:
        print("Nenhum treino agendado.")
        return

    for item in agenda:
        print(item[0], "->", item[1])    

def pesquisar_exercicio():
     print("\n=== PESQUISAR EXERCICIO ===")
   

     nome = input("DIgite o nome do exercicio: ")

     cursor.execute( """
        SELECT id,exercicio, carga, series, repeticoes, data_treino
        FROM treinos
        WHERE exercicio LIKE %s
     """,
        ("%"+ nome + "%",) 
     )
     resultados = cursor.fetchall()

     if len(resultados) == 0:
         print("Nenhum treino encontrado.")
         return
     for treino in resultados:
        print("\n------------------")
        print("ID:", treino[0])
        print("Exercicio:", treino[1])
        print("Carga:", treino[2], "kg")
        print("Series:", treino[3])
        print("Repeticoes:", treino[4])
        print("Data:", treino[5])
def evolucao_exercicio():
     print("\n=== EVOLUCAO DO EXERCICIO ===")

     nome = input("DIgite o nome do exercicio:")

     cursor.execute(
          """
          SELECT exercicio,carga,data_treino
          FROM treinos
          WHERE exercicio LIKE %s
          ORDER BY data_treino
          """,
          ("%" + nome + "%",)
     )

     resultados = cursor.fetchall()
     if len(resultados) == 0:
            print("nenhum registro encontrado.")
            return
     
     print("\n=== HISTORICO ===")

     for treino in resultados:
        print(
            treino[2],
            "->",
            treino[0],
            "-",
            treino[1],
            "kg"
        )  
def estatistica ():
     print("\n=== ESTATISTICAS ===") 
     cursor.execute("""
     SELECT COUNT(*)
     FROM treinos
     """)
  
     total = cursor.fetchone()

     print("exercicios registrados:", total[0])  

     cursor.execute("""
     SELECT COUNT(*)
     FROM agenda_treinos
     """)

     agendados = cursor.fetchone()

     print("treinos agendados:", agendados[0]) 
     cursor.execute("""
     SELECT exercicio, COUNT(*)
     FROM treinos
     GROUP BY exercicio
     ORDER BY COUNT(*) DESC
     LIMIT 1
     """)
     mais_realizado = cursor.fetchone()

     print("Exercicio mais realizado:", mais_realizado[0]) 
     print("Quantidade:", mais_realizado[1])
def sequencia ():
     print("\n=== SEQUENCIA ===")

     cursor.execute("""
     SELECT DISTINCT data_treino
     FROM treinos
     ORDER BY data_treino DESC
     """)
     datas= cursor.fetchall()
    

     if len(datas) == 0:
          print("Nenhum treino registrado ")
          return
     sequencia = 1
     sequencia_atual= 1
     melhor_sequencia= 1

     for i in range(len(datas) - 1):
          
          diferenca = (datas[i][0] - datas [i + 1][0]).days
                       
          if diferenca ==1:
               sequencia += 1
               sequencia_atual+=1

               if sequencia_atual > melhor_sequencia:
                    melhor_sequencia = sequencia_atual
          else:
               sequencia_atual = 1
     print("\n🔥 sequencia atual:",sequencia, "dias")
     print("🏆 Melhor sequencia:", melhor_sequencia, "dias")
     print("\nHistorico:")
     for data in datas:
          print("✅", data[0])
def dashboard():

    print("\n=== DASHBOARD ===")

    # Exercícios registrados
    cursor.execute("""
    SELECT COUNT(*)
    FROM treinos
    """)
    total = cursor.fetchone()

    # Treinos agendados
    cursor.execute("""
    SELECT COUNT(*)
    FROM agenda_treinos
    """)
    agendados = cursor.fetchone()

    # Exercício mais realizado
    cursor.execute("""
    SELECT exercicio, COUNT(*)
    FROM treinos
    GROUP BY exercicio
    ORDER BY COUNT(*) DESC
    LIMIT 1
    """)
    mais_realizado = cursor.fetchone()

    # Último treino
    cursor.execute("""
    SELECT data_treino
    FROM treinos
    ORDER BY data_treino DESC
    LIMIT 1
    """)
    ultimo_treino = cursor.fetchone()

    # Sequência
    cursor.execute("""
    SELECT DISTINCT data_treino
    FROM treinos
    ORDER BY data_treino DESC
    """)
    datas = cursor.fetchall()

    sequencia = 0

    if len(datas) > 0:

        sequencia = 1

        for i in range(len(datas) - 1):

            diferenca = (datas[i][0] - datas[i + 1][0]).days

            if diferenca == 1:
                sequencia += 1
            else:
                break

    print("\n🏋 Exercicios registrados:", total[0])

    print("📅 Treinos agendados:", agendados[0])

    if mais_realizado:
        print("📈 Exercicio mais realizado:",
              mais_realizado[0])

    print("🔥 Sequencia atual:", sequencia, "dias")

    if ultimo_treino:
        print("📆 Ultimo treino:",
              ultimo_treino[0])
    print("=== GYMTRACKER === ")
    print("1 - Cadastrar treino")
    print("2 - Ver Treinos")
    print("3 - Editar Treino")
    print("4 - Excluir Treino")
    print("5 - Agendar Treino")
    print("6 - ver agenda")
    print("7 - Pesquisar Exercicio")
    print("8 Evolucao do Exercicio")
    print("9 - Estatistica")
    print("10 - Sequencia")
    print("11 - Dashboard")
    print("12 - Sair")

while True:

    opcao = input("Escolha uma opção:")
    
    if opcao == "1" :
        cadastrar_treino()
    
    if opcao == "2":
               mostrar_treinos()
    if opcao =="3":
         editar_treino()           
    if opcao == "4":
            excluir_treino()
    if opcao =="5":
         agendar_treino()
    if opcao =="6":
         ver_agenda() 
    if opcao == "7":
         pesquisar_exercicio()
    if opcao =="8":
         evolucao_exercicio()
    if opcao =="9":
         estatistica()
    if opcao =="10":
         sequencia()
    if opcao=="11":
         dashboard()
    if opcao == "12":
       break
        


        
        