import ast
import json
from math import sqrt
import re
from typing import Dict, List
from autogen import ConversableAgent
import sys
import os
from dotenv import load_dotenv

load_dotenv()

def fetch_restaurant_data(restaurant_name: str) -> Dict[str, List[str]]:
    reviews = []
    pattern = re.compile(rf"^{re.escape(restaurant_name)}\.\s*(.*)", re.IGNORECASE)
    with open("restaurantes.txt", encoding="utf-8") as f:
        for line in f:
            match = pattern.match(line.strip())
            if match:
                reviews.append(match.group(1))
    return {restaurant_name: reviews}


def calculate_overall_score(restaurant_name: str, food_scores: List[int], customer_service_scores: List[int]) -> Dict[str, float]:
    n = min(len(food_scores), len(customer_service_scores))
    if n == 0:
        return {restaurant_name: 0.0}
    total = sum(sqrt(food_scores[i]**2 * customer_service_scores[i]) for i in range(n))
    score = total * (1 / (n * sqrt(125))) * 10
    return {restaurant_name: round(score, 3)}


def extract_restaurant_name(query: str) -> str:
    patterns = [
        r"do\s+(.+?)[\?\.]?$",
        r"do restaurante\s+(.+?)[\?\.]?$",
        r"restaurante\s+(.+?)[\?\.]?$",
        r"média\s+do\s+(.+?)[\?\.]?$",
    ]
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return query.strip()


def main(user_query: str):
    restaurant_name = extract_restaurant_name(user_query)

    llm_config = {
        "config_list": [{
            "model": "gpt-3.5-turbo",
            "api_key": os.environ.get("OPENAI_API_KEY"),
        }],
        "temperature": 0
    }

    data_fetch_agent = ConversableAgent(
        name="data_fetch_agent",
        system_message="Você busca avaliações de restaurantes com base no nome.",
        llm_config=llm_config
    )
    data_fetch_agent.register_for_execution(name="fetch_restaurant_data")(fetch_restaurant_data)

    review_analysis_agent = ConversableAgent(
        name="review_analysis_agent",
        system_message=(
            "Você recebe avaliações de restaurantes e converte adjetivos presentes nas frases "
            "em notas de 1 a 5, com base nesta escala:\n"
            "1: horrível, nojento, terrível\n"
            "2: ruim, desagradável, ofensivo\n"
            "3: mediano, sem graça, irrelevante\n"
            "4: bom, agradável, satisfatório\n"
            "5: incrível, impressionante, surpreendente\n\n"
            "Ignore adjetivos fora dessa lista (como 'atencioso', 'rápido', etc).\n"
            "Identifique se cada adjetivo se refere à comida ou ao atendimento, com base na frase.\n\n"
            "Retorne um JSON no formato:\n"
            "{ \"food_scores\": [...], \"customer_service_scores\": [...] }"
        ),
        llm_config=llm_config
    )

    score_agent = ConversableAgent(
        name="score_agent",
        system_message="Você calcula a nota final com base nas listas de notas de comida e atendimento.",
        llm_config=llm_config
    )
    score_agent.register_for_execution(name="calculate_overall_score")(calculate_overall_score)

    *_, reviews_dict = data_fetch_agent.execute_function({
        "name": "fetch_restaurant_data",
        "arguments": json.dumps({"restaurant_name": restaurant_name})
    })
    reviews_content_str = reviews_dict.get("content", "{}")
    reviews_content_dict = ast.literal_eval(reviews_content_str)
    reviews = reviews_content_dict.get(restaurant_name, [])

    review_prompt = (
        f"Avaliações do restaurante {restaurant_name}:\n\n"
        + "\n".join(reviews) +
        "\n\nConverta os adjetivos relevantes da escala acima em notas e retorne um JSON como:"
        "\n{ \"food_scores\": [...], \"customer_service_scores\": [...] }"
    )

    review_response = review_analysis_agent.generate_reply(messages=[{"role": "user", "content": review_prompt}])
    score_lists_content_dict = json.loads(review_response)
    food_scores = score_lists_content_dict.get("food_scores", [])
    customer_scores = score_lists_content_dict.get("customer_service_scores", [])

    *_, final_score = score_agent.execute_function({
        "name": "calculate_overall_score",
        "arguments": json.dumps({
            "restaurant_name": restaurant_name,
            "food_scores": food_scores,
            "customer_service_scores": customer_scores
        })
    })

    print(final_score.get("content", "{}"))


if __name__ == "__main__":
    assert len(sys.argv) > 1, "Certifique-se de incluir uma consulta para algum restaurante ao executar a função main."
    main(sys.argv[1])
