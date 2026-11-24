"""HTTP-level checks for quiz membership and availability."""
import sqlite3
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
import database
import main
from session_security import sign_cookie


@pytest.fixture
def quiz_env(tmp_path, monkeypatch):
    path = str(tmp_path / "quiz.db")
    conn = sqlite3.connect(path)
    database.init_db_tables(conn)
    for uid, role, cls in [(1,"student","10A"),(2,"student","10B"),(3,"teacher",None)]:
        conn.execute("INSERT INTO users (id,name,username,password,role,class_name) VALUES (?,?,?,?,?,?)", (uid,"Demo",f"u{uid}","test-only",role,cls))
    start=(datetime.now()-timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
    end=(datetime.now()+timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
    conn.execute("INSERT INTO quizzes (id,title,class_name,duration_minutes,start_date,end_date,has_negative_marking,negative_mark_value,teacher_id) VALUES (1,'Test','10A',20,?,?,1,0.5,3)",(start,end))
    conn.execute("INSERT INTO questions (id,quiz_id,question_text,option_a,option_b,option_c,option_d,correct_option,points) VALUES (1,1,'Test?','a','b','c','d','A',1)")
    conn.commit();conn.close()
    monkeypatch.setattr(database,'get_db_path',lambda:path)
    clock=[100000.0]
    with TestClient(main.app) as client:
        client.cookies.set('user_id',sign_cookie('1','user_id'))
        yield client,path,clock


def scalar(path, sql):
    with sqlite3.connect(path) as conn:
        return conn.execute(sql).fetchone()[0]


def test_valid_open_submit_result_duplicate(quiz_env):
    client,path,clock=quiz_env
    assert client.get('/quiz/1').status_code==200
    response=client.post('/quiz/1/submit',data={'q_1':'A'},follow_redirects=False)
    assert response.status_code==303
    assert response.headers['location']=='/quiz/1/result'
    assert client.get('/quiz/1/result').status_code==200
    assert scalar(path,'SELECT score FROM submissions')==1.0
    assert client.post('/quiz/1/submit',data={'q_1':'B'},follow_redirects=False).status_code==303
    assert scalar(path,'SELECT COUNT(*) FROM submissions')==1
    assert scalar(path,'SELECT score FROM submissions')==1.0


def test_cross_class_get_and_direct_post_rejected(quiz_env):
    client,path,clock=quiz_env
    client.cookies.clear();client.cookies.set('user_id',sign_cookie('2','user_id'))
    assert client.get('/quiz/1').status_code==404
    assert client.post('/quiz/1/submit',data={'q_1':'A'}).status_code==404
    assert scalar(path,'SELECT COUNT(*) FROM submissions')==0


@pytest.mark.parametrize('column,value',[('start_date','2999-01-01 00:00'),('end_date','2000-01-01 00:00')])
def test_window_rechecked_on_post(quiz_env,column,value):
    client,path,clock=quiz_env
    assert client.get('/quiz/1').status_code==200
    with sqlite3.connect(path) as conn:
        conn.execute(f'UPDATE quizzes SET {column}=?',(value,))
    assert client.post('/quiz/1/submit',data={'q_1':'A'}).status_code==403
    assert scalar(path,'SELECT COUNT(*) FROM submissions')==0


@pytest.mark.parametrize('column,value',[('start_date','2999-01-01 00:00'),('end_date','2000-01-01 00:00')])
def test_single_bound_window_checked(quiz_env,column,value):
    client,path,clock=quiz_env
    other='end_date' if column=='start_date' else 'start_date'
    with sqlite3.connect(path) as conn:
        conn.execute(f'UPDATE quizzes SET {column}=?, {other}=?',(value,''))
    assert client.get('/quiz/1').status_code==403
    assert client.post('/quiz/1/submit',data={'q_1':'A'}).status_code==403
    assert scalar(path,'SELECT COUNT(*) FROM submissions')==0


def test_wrong_role_and_missing_quiz(quiz_env):
    client,path,clock=quiz_env
    assert client.post('/quiz/999/submit').status_code==404
    client.cookies.clear();client.cookies.set('user_id',sign_cookie('3','user_id'))
    response=client.post('/quiz/1/submit',follow_redirects=False)
    assert response.status_code==303 and response.headers['location']=='/login'

