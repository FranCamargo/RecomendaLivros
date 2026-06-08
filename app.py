from flask import Flask, render_template, request, jsonify
import sqlite3 as sqlite3
import pandas as pd
from flask_cors import CORS
from fuzzywuzzy import process

app = Flask(__name__)
CORS(app) #permite a conexão das rotas

#Rota pra rodar o html
@app.route("/")
def home():
    return render_template("index.html", resultado=None)

#Rota para ativar a função do recomendador
@app.route("/pesquisar", methods=["POST"])
def pesquisar():
    entrada = request.json.get("entrada")
    criterio = request.json.get("criterio")

    #Conecta ao banco e carrega os dados da query pra variável ser usada depois
    conn = sqlite3.connect("biblioteca.db")
    print("Conexão com o banco de dados estabelecida com sucesso.")
    df_livros = pd.read_sql_query("""
        SELECT l.id, l.title, l.authors, c.name AS categoria, 
               AVG(d.nota) AS media_avaliacao, COUNT(d.id) AS total_downloads
        FROM livros l
        JOIN categorias c ON l.categoria_id = c.id
        LEFT JOIN downloads d ON l.id = d.livro_id
        GROUP BY l.id
        """, conn)
    conn.close()

    # Função que recomenda os livros
    def recomendar_livros(entrada, criterio):
        entrada = str(entrada).strip().lower() # Faz um tratamento pra transformar a entrada em minúsculas
        if not entrada:
            return exibir_recomendacoes(
                "Nenhum termo foi inserido.\n\nAbaixo deixamos como recomendação nossos livros mais populares:\n",
                df_livros.sort_values(by=["media_avaliacao", "total_downloads"], ascending=False).head(5)
            )

        if criterio == 1:  # Pesquisa por Título
            # Encontra a melhor correspondência para o título inserido 
            similaridade = process.extractOne(entrada, df_livros['title'].str.lower(), score_cutoff=60)
            if similaridade:
                # Seleciona o livro que corresponde ao título encontrado
                livro = df_livros[df_livros['title'].str.lower() == similaridade[0]].iloc[0]
                # Pega a categoria do livro encontrado
                categoria = livro['categoria']
                # Busca recomendações de livros na mesma categoria
                recomendacoes = df_livros[df_livros['categoria'] == categoria].head(5)
                # Verifica se a similaridade é maior que 80%
                if similaridade[1] > 80:
                    return exibir_recomendacoes(
                    f"O livro '{similaridade[0].title()}' foi encontrado.\nConfira abaixo as recomendações de livros na mesma categoria:\n", 
                    recomendacoes
                    )
                else: #Resposta genérica 
                    return exibir_recomendacoes(
                        f"Aqui estão os resultados da busca '{entrada}' por Título:\n", 
                    recomendacoes
                     )

        if criterio == 2:  # Pesquisa por Autor
            similaridade = process.extractOne(entrada, df_livros['authors'].str.lower(), score_cutoff=60)
            if similaridade:
                if similaridade[1] >= 80:  # Formata a resposta diferente se a similaridade for maior ou igual a 80%
                    return exibir_recomendacoes(f"Autor '{similaridade[0].title()}' encontrado.\nConfira abaixo as recomendações de obras desse autor com as melhores avaliações:\n", 
                                                df_livros[df_livros['authors'].str.lower().str.contains(similaridade[0], case=False, na=False)].head(5))
                else:  # Responde de forma generalizada sobre o termo pesquisado
                    return exibir_recomendacoes(f"Aqui estão os resultados da busca '{entrada}' por Autor:\n", 
                                                df_livros[df_livros['authors'].str.lower().str.contains(similaridade[0], case=False, na=False)].head(5))

        if criterio == 3:  # Pesquisa por Categoria
            similaridade = process.extractOne(entrada, df_livros['categoria'].str.lower(), score_cutoff=60)
            if similaridade:
                recomendacoes = df_livros[df_livros['categoria'].str.lower() == similaridade[0]].head(5)
                return exibir_recomendacoes(f"Aqui estão os resultados da busca '{entrada}' por Categoria:\n", recomendacoes)

        recomendacoes = df_livros.sort_values(by=["media_avaliacao", "total_downloads"], ascending=False).head(5)
        return exibir_recomendacoes(f"Nenhum resultado encontrado para '{entrada}'.\n\nAbaixo deixamos recomendações dos livros mais populares em nossa biblioteca:\n", recomendacoes)


    # Função para exibir recomendações
    def exibir_recomendacoes(mensagem, recomendacoes):
        recomendacoes["media_avaliacao"] = recomendacoes["media_avaliacao"].apply(lambda x: round(x, 2) if pd.notna(x) else 0.0)
        relevancias = recomendacoes["media_avaliacao"].astype(float).tolist()
        
        
        return {
            "mensagem": mensagem,
            "recomendacoes": recomendacoes[['title', 'authors', 'categoria', 'media_avaliacao']].rename(
                columns={"title": "Título", "authors": "Autor", "categoria": "Categoria", "media_avaliacao": "Avaliação"}
            ).to_dict(orient="records"),
            
        }

    #Remove possíveis duplicatas e mantém apenas os livros com maior avaliação
    df_livros = df_livros.sort_values(by=["media_avaliacao"], ascending=False).drop_duplicates(subset=["title"], keep="first")

    #Remove livros com avaliação inferior a 3.7
    df_livros = df_livros[df_livros["media_avaliacao"] >=2.59]

    #Chama a função de recomendação
    resultado = recomendar_livros(entrada, criterio)
    return jsonify(resultado)

#roda o app Flask
if __name__ == "__main__":
    app.run(debug=True)
