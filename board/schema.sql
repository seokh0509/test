Create table 'board' ('idx' integer PRIMARY KEY, 'title' varchar(30) Not Null, 'cont' text(1000) Not null, 'uid' varchar(20) Not NUll, 'time' TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, 'hit' integer NOT NULL default '0', 'file' varchar(200), 'fn' varchar(50));

create table 'comments' ('idx' integer PRIMARY KEY, 'pid' int(10) default null, 'bid' int(10) Not Null, 'cont' varchar(200) Not Null, 'uid' varchar(20) Not Null, 'time' TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE 'userlist' ('u_id' varchar(20) not null, 'u_pw' varchar(100) not null, 'u_mail' varchar(50) Not NUll, 'u_phone' varchar(20) Not Null);
