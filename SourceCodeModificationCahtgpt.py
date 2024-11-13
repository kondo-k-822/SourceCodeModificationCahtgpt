import openai
import os
import runpy
import tkinter as tk
from tkinter import filedialog

'''
前提
・本プログラムはpyスクリプト修正専用のプログラムである
・widows端末で使用する場合「setx OPENAI_API_KEY {APIキー}」を実行すること
※APIキーは担当者（近藤）に問い合わせること

処理概要 
1. エラーとなるソースコードを選択
----------------------繰り返す-----------------------------
2. chatGPT_APIに１のソースコードと修正内容をリクエスト
3. 2のレスポンス（修正コード）をファイルに書き込む
   ファイル名：xxxx_modified.py
4. 3のファイル実行する
   成功の場合 : 処理を終了する
   エラーの場合：2の処理に戻る
----------------------繰り返す-----------------------------
'''

# OpenAI APIキーを環境変数から取得する
openai.api_key = os.getenv("OPENAI_API_KEY")

def read_file():
    # Tkinterのウィンドウを作成
    root = tk.Tk()
    root.withdraw()  # メインウィンドウを非表示にする

    # ファイル選択ダイアログを表示
    file_path = filedialog.askopenfilename(
        title="ファイルを選択",
        filetypes=[("Python files", "*.py")]
    )

    if file_path:  # ファイルが選択された場合
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                file_content = file.read()  # ファイルの内容を読み込む
            return file_content, file_path  # 内容とファイルパスを返す
        except (IOError, UnicodeDecodeError) as e:
            print(f"ファイルの読み込み中にエラーが発生しました: {e}")
    else:
        print("ファイルが選択されませんでした。")

    return None, None

def generate_response(file_content):
    content = f"次のPythonコードを修正してください。ただし、修正したプログラムのみを返してください：{file_content}"

    try:
        # チャットのレスポンスを生成
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": content},
            ],
            temperature=1
        )

        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"応答生成中にエラーが発生しました: {e}")
        return None

def write_to_file(data, file_path):
    # 書き込むファイルのパスを元のファイルのディレクトリに設定
    directory = os.path.dirname(file_path)
    # 元のファイル名に'_modified'を付けて新しいファイル名を作成
    file_name = os.path.basename(file_path)
    new_file_name = os.path.join(directory, f"{os.path.splitext(file_name)[0]}_modified.py")

    try:
        with open(new_file_name, 'w', encoding='utf-8') as file:
            file.write(data)
        print(f"{new_file_name} にデータを書き込みました。")
        return new_file_name
    except IOError as e:
        print(f"ファイルの書き込み中にエラーが発生しました: {e}")

def response_check(response_content):
    if response_content:
        python_new_file = write_to_file(response_content, file_path)
        print(python_new_file)
        return python_new_file
    else:
        print("プログラムを終了します。") 
        return None

# 処理開始       
# ファイルの内容を読み取る
file_content, file_path = read_file()

#ファイルが選択されていない場合 : 処理は終了
#ファイルが選択されている場合 : 選択したソースをAPIに投げ修正依頼を投げレスポンスを受け取り成功するまで実行
if not file_content:
    print("プログラムを終了します。")
else: 
    max_retries = 3  # 最大リトライ回数
    count = 0

    #デフォルトではソースの成功する判定ループは3回繰り返す
    #必要であれば改修
    while count < max_retries:
        #chatGPT_APIへリクエストを投げる
        response_content = generate_response(file_content)
        #修正したソースコードをファイルに書き込む
        python_new_file = response_check(response_content)

        #修正したソースファイル実行する
        #成功した場合：処理終了
        #失敗した場合：再度失敗したソースファイル元にchatGPT_APIへリクエスト
        if python_new_file:
            try:
                runpy.run_path(python_new_file) #修正したソースファイルを実行
                break  # 実行が成功したらループを抜ける
            except Exception as e:
                print(f"スクリプトの実行中にエラーが発生しました。リトライします: {e}")
                count += 1
                if count >= max_retries:
                    print("最大リトライ回数に達しました。プログラムを終了します。")
        else:
            print("応答に問題がありました。プログラムを終了します。")
            break