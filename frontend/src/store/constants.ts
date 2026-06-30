// api根路径 需要和pycharm的一致
const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

const USER_ID = 'user_id'
const USER_NAME = 'user_name'
const USER_TOKEN = 'user_token'
const USER_ALLOW_CLASS_PASS = 'user_allow_class_pass'

const ADMIN_USER_ID = 'admin_user_id'
const ADMIN_USER_NAME = 'admin_user_name'
const ADMIN_USER_TOKEN = 'admin_user_token'
const ADMIN_USER_ROLE = 'admin_user_role'


export {BASE_URL, USER_TOKEN, USER_NAME, USER_ID, USER_ALLOW_CLASS_PASS, ADMIN_USER_ID,ADMIN_USER_NAME,ADMIN_USER_TOKEN, ADMIN_USER_ROLE }
